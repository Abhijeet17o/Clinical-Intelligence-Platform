"""
Explainability Engine

Main interface for generating explanations for medicine recommendations.
Combines LIME explanations with natural language generation.
"""

import os
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

from .lime_explainer import LimeExplainer

logger = logging.getLogger(__name__)


class RecommendationExplainer:
    """
    Main explainability engine for medicine recommendations.
    
    Combines:
    - LIME-based feature importance
    - Natural language explanation generation via Gemini
    - Voting breakdown from ensemble
    """
    
    def __init__(self, use_gemini: bool = True):
        """
        Initialize the explainer.
        
        Args:
            use_gemini: Whether to use Gemini for natural language explanations
        """
        self.lime = LimeExplainer()
        self.use_gemini = use_gemini
        self._gemini_configured = False
    
    def _configure_gemini(self):
        """Configure Gemini API if not already done."""
        if self._gemini_configured:
            return True
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, will use template explanations")
            return False
        
        try:
            genai.configure(api_key=api_key)
            self._gemini_configured = True
            return True
        except Exception as e:
            logger.error(f"Error configuring Gemini: {e}")
            return False
    
    def _generate_nl_explanation(
        self,
        medicine: Dict,
        symptoms: str,
        feature_importance: Dict[str, float],
        voting: Dict[str, float]
    ) -> str:
        """Generate natural language explanation using Gemini."""
        if not self.use_gemini or not self._configure_gemini():
            return self._template_explanation(medicine, feature_importance, voting)
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Prepare top symptoms
            top_symptoms = sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            symptom_str = ', '.join([s[0] for s in top_symptoms])
            
            # Prepare voting summary
            top_model = max(voting.items(), key=lambda x: x[1])
            
            prompt = f"""Generate a brief, professional medical explanation (1-2 sentences) 
            for why {medicine['name']} is recommended.
            
            Medicine: {medicine['name']}
            Description: {medicine.get('description', 'N/A')}
            Patient symptoms: {symptom_str}
            Best matching model: {top_model[0]} with score {top_model[1]:.2f}
            
            Keep it concise, professional, and suitable for a doctor to read.
            Do not include disclaimers or warnings."""
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.warning(f"Gemini explanation failed: {e}")
            return self._template_explanation(medicine, feature_importance, voting)
    
    def _template_explanation(
        self,
        medicine: Dict,
        feature_importance: Dict[str, float],
        voting: Dict[str, float]
    ) -> str:
        """Generate template-based explanation when Gemini is unavailable."""
        top_symptoms = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        if top_symptoms:
            symptom_str = ', '.join([s[0] for s in top_symptoms])
            return f"{medicine['name']} is recommended based on symptoms: {symptom_str}."
        else:
            return f"{medicine['name']} matches the overall symptom profile."
    
    def explain_recommendation(
        self,
        symptoms: str,
        medicine: Dict,
        final_score: float,
        voting: Dict[str, float],
        recommender_func=None
    ) -> Dict:
        """
        Generate a complete explanation for a single recommendation.
        
        Args:
            symptoms: Patient symptoms string
            medicine: Medicine dictionary
            final_score: Final ensemble score
            voting: Individual model scores
            recommender_func: Optional function for LIME perturbation analysis
            
        Returns:
            Dict with complete explanation:
            - primary_reason: Main reason for recommendation
            - contributing_symptoms: List of relevant symptoms
            - feature_importance: Token importance weights
            - model_contributions: Which models contributed most
            - confidence: Overall confidence score
            - natural_language: Human-readable explanation
        """
        # Default feature importance from voting
        if not voting:
            voting = {'ensemble': final_score}
        
        # Get model contributions
        model_contributions = {
            model: score for model, score in voting.items()
        }
        
        # Get LIME-based feature importance if recommender function available
        if recommender_func:
            lime_result = self.lime.explain(
                symptoms, medicine, final_score, recommender_func
            )
            feature_importance = lime_result['feature_importance']
            contributing_symptoms = lime_result['contributing_symptoms']
        else:
            # Fallback: extract keywords from symptoms
            feature_importance = self._extract_keywords(symptoms)
            contributing_symptoms = list(feature_importance.keys())[:5]
        
        # Calculate confidence based on model agreement
        scores = list(voting.values())
        if len(scores) > 1:
            # Higher confidence if models agree
            confidence = 1 - (max(scores) - min(scores))
        else:
            confidence = final_score
        
        # Generate natural language explanation
        nl_explanation = self._generate_nl_explanation(
            medicine, symptoms, feature_importance, voting
        )
        
        # Determine primary reason
        if contributing_symptoms:
            primary_reason = f"High match for {contributing_symptoms[0]}"
            if len(contributing_symptoms) > 1:
                primary_reason += f" and {contributing_symptoms[1]}"
        else:
            primary_reason = "General symptom profile match"
        
        return {
            'primary_reason': primary_reason,
            'contributing_symptoms': contributing_symptoms,
            'feature_importance': feature_importance,
            'model_contributions': model_contributions,
            'confidence': round(confidence, 2),
            'natural_language': nl_explanation
        }
    
    def _extract_keywords(self, text: str) -> Dict[str, float]:
        """Simple keyword extraction as fallback."""
        # Medical keywords to look for
        medical_terms = [
            'fever', 'headache', 'pain', 'cough', 'cold', 'nausea',
            'vomiting', 'diarrhea', 'fatigue', 'weakness', 'dizzy',
            'swelling', 'rash', 'infection', 'inflammation'
        ]
        
        text_lower = text.lower()
        found = {}
        
        for term in medical_terms:
            if term in text_lower:
                found[term] = 0.2  # Equal weight for simple extraction
        
        # Normalize
        if found:
            total = sum(found.values())
            found = {k: v/total for k, v in found.items()}
        
        return found
    
    def explain_batch(
        self,
        symptoms: str,
        recommendations: List[Dict],
        recommender_func=None
    ) -> List[Dict]:
        """
        Generate explanations for a batch of recommendations.
        
        Args:
            symptoms: Patient symptoms string
            recommendations: List of recommendation dicts from ensemble
            
        Returns:
            List of recommendation dicts with added 'explanation' field
        """
        explained_recommendations = []
        
        for rec in recommendations:
            explanation = self.explain_recommendation(
                symptoms=symptoms,
                medicine={'name': rec['name'], 'description': rec.get('description', '')},
                final_score=rec['final_score'],
                voting=rec.get('voting', {}),
                recommender_func=recommender_func
            )
            
            rec_with_explanation = rec.copy()
            rec_with_explanation['explanation'] = explanation
            explained_recommendations.append(rec_with_explanation)
        
        return explained_recommendations
