"""
LIME-based Explainer

Provides local interpretable explanations for medicine recommendations
using a simplified LIME-like approach optimized for prototype.
"""

import numpy as np
from typing import List, Dict, Tuple, Callable
import logging
import re
from lime import lime_text

logger = logging.getLogger(__name__)


class LimeExplainer:
    """
    Wrapper for the official LIME (Local Interpretable Model-agnostic Explanations) library.
    
    This explainer:
    1. Uses LimeTextExplainer to build a local linear model.
    2. Identifies symptom keywords that contribute positively or negatively to recommendations.
    3. Provides granular feature importance weights.
    """
    
    def __init__(self, num_samples: int = 50):
        """
        Initialize the LIME explainer.
        
        Args:
            num_samples: Number of perturbed samples to generate for the local model
        """
        self.explainer = lime_text.LimeTextExplainer(
            class_names=['Score'],
            char_level=False
        )
        self.num_samples = num_samples
    
    def explain(
        self,
        symptoms: str,
        medicine: Dict,
        score: float,
        recommender_func: Callable
    ) -> Dict:
        """
        Generate a formal LIME explanation for a recommendation.
        
        Args:
            symptoms: Original symptom text
            medicine: Medicine being explained
            score: Original recommendation score (final ensemble score)
            recommender_func: Function that takes (list of symptoms_strings, list of medicines) 
                               and returns a 2D array of scores (samples x 1)
            
        Returns:
            Dict with:
            - feature_importance: Dict of token -> importance weight
            - contributing_symptoms: List of most important symptoms
            - explanation_text: Human-readable explanation
        """
        if not symptoms or not symptoms.strip():
             return {
                'feature_importance': {},
                'contributing_symptoms': [],
                'explanation_text': 'No symptoms provided for analysis.'
            }

        try:
            # LIME classifier_fn expects a list of strings and returns (n_samples, n_classes)
            # We treat the medicine score as the "probability" of the first class.
            def classifier_fn(texts: List[str]):
                # meds is a list containing only the medicine we are explaining
                # We need to compute scores for each text in the perturbed batch
                all_scores = []
                for text in texts:
                    # lime_scorer in app.py returns a list of floats for the medicines provided
                    text_scores = recommender_func(text, [medicine])
                    # Ensure we have a score (0.0 fallback)
                    s = float(text_scores[0]) if text_scores else 0.0
                    # LIME needs a 2D array [samples, classes]
                    # Since it's a regression-like score, we provide it as the "positive" class
                    # and (1-s) as the "negative" class for a pseudo-probability distribution
                    all_scores.append([1.0 - s, s])
                return np.array(all_scores)

            # Generate explanation
            # labels=[1] because class 1 is the 'Score' (the positive recommendation)
            exp = self.explainer.explain_instance(
                symptoms, 
                classifier_fn, 
                num_features=10,
                num_samples=self.num_samples,
                labels=(1,)
            )
            
            # Extract weights for the 'Score' class
            # list of (word, weight)
            weights = exp.as_list(label=1)
            
            # Convert to dict and filter small weights
            importance = {word: float(weight) for word, weight in weights if abs(weight) > 0.01}
            
            # Get top contributing symptoms (positive weights)
            top_symptoms = [word for word, weight in weights if weight > 0.02][:5]
            
            # Generate explanation text
            if top_symptoms:
                symptom_str = ', '.join(top_symptoms[:3])
                explanation = f"Recommended based on similarity to: {symptom_str}"
            else:
                 explanation = "Based on general symptom patterns."

            return {
                'feature_importance': importance,
                'contributing_symptoms': top_symptoms,
                'explanation_text': explanation
            }

        except Exception as e:
            logger.error(f"LIME explanation failed: {e}", exc_info=True)
            return {
                'feature_importance': {},
                'contributing_symptoms': [],
                'explanation_text': 'Explanation currently unavailable.'
            }

    def explain_batch(
        self,
        symptoms: str,
        recommendations: List[Dict],
        recommender_func: Callable
    ) -> List[Dict]:
        """
        Generate explanations for a batch of recommendations.
        """
        results = []
        for rec in recommendations:
            res = self.explain(symptoms, rec, rec.get('final_score', 0), recommender_func)
            results.append(res)
        return results
