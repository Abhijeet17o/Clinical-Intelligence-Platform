"""
Knowledge-Based Recommender

Uses a rule-based system with predefined symptom-to-medicine mappings
based on medical knowledge.
"""

import numpy as np
from typing import List, Dict, Set
import logging
import re

from .base_recommender import BaseRecommender

logger = logging.getLogger(__name__)


# Medical knowledge base: symptom keywords mapped to medicine categories
SYMPTOM_MEDICINE_RULES = {
    # Pain & Fever
    'fever': {'analgesic', 'antipyretic', 'paracetamol', 'acetaminophen', 'ibuprofen'},
    'headache': {'analgesic', 'pain relief', 'paracetamol', 'aspirin', 'ibuprofen', 'migraine'},
    'pain': {'analgesic', 'pain relief', 'paracetamol', 'ibuprofen', 'diclofenac'},
    'body ache': {'analgesic', 'pain relief', 'muscle relaxant', 'paracetamol'},
    'muscle pain': {'muscle relaxant', 'pain relief', 'analgesic'},
    'chills': {'paracetamol', 'antipyretic', 'flu relief'},
    'weakness': {'multivitamin', 'supplement', 'electrolyte'},
    
    # Respiratory
    'cough': {'antitussive', 'cough syrup', 'expectorant', 'dextromethorphan'},
    'cold': {'decongestant', 'antihistamine', 'cold relief'},
    'congestion': {'decongestant', 'nasal spray', 'pseudoephedrine'},
    'sore throat': {'antiseptic', 'lozenge', 'throat relief'},
    'runny nose': {'antihistamine', 'decongestant'},
    
    # Gastrointestinal
    'nausea': {'antiemetic', 'domperidone', 'ondansetron'},
    'vomiting': {'antiemetic', 'domperidone'},
    'diarrhea': {'antidiarrheal', 'loperamide', 'oral rehydration'},
    'stomach': {'antacid', 'proton pump inhibitor', 'omeprazole'},
    'acidity': {'antacid', 'ranitidine', 'omeprazole'},
    'indigestion': {'digestive', 'antacid', 'enzyme'},
    
    # Allergies
    'allergy': {'antihistamine', 'cetirizine', 'loratadine', 'fexofenadine'},
    'itching': {'antihistamine', 'antipruritic', 'calamine'},
    'rash': {'antihistamine', 'corticosteroid', 'calamine'},
    'hives': {'antihistamine', 'epinephrine'},
    
    # Infections
    'infection': {'antibiotic', 'antimicrobial', 'antiseptic'},
    'bacterial': {'antibiotic', 'amoxicillin', 'azithromycin'},
    'viral': {'antiviral', 'oseltamivir'},
    'fungal': {'antifungal', 'clotrimazole', 'fluconazole'},
    
    # Chronic Conditions
    'diabetes': {'antidiabetic', 'metformin', 'insulin', 'blood sugar'},
    'hypertension': {'antihypertensive', 'blood pressure', 'amlodipine', 'losartan'},
    'asthma': {'bronchodilator', 'inhaler', 'salbutamol', 'corticosteroid'},
    
    # Sleep & Anxiety
    'insomnia': {'sedative', 'sleep aid', 'melatonin'},
    'anxiety': {'anxiolytic', 'alprazolam', 'diazepam'},
    'stress': {'anxiolytic', 'adaptogen'},
    
    # Other
    'inflammation': {'anti-inflammatory', 'nsaid', 'corticosteroid'},
    'swelling': {'anti-inflammatory', 'nsaid', 'diuretic'},
    'fatigue': {'vitamin', 'multivitamin', 'iron', 'supplement'},
    'weakness': {'vitamin', 'supplement', 'iron', 'b12'},
}


class KnowledgeRecommender(BaseRecommender):
    """
    Rule-based recommender using medical knowledge mapping.
    
    Maps symptom keywords to medicine categories and scores medicines
    based on how many rules they match.
    """
    
    def __init__(self, custom_rules: Dict[str, Set[str]] = None):
        """
        Initialize the knowledge recommender.
        
        Args:
            custom_rules: Optional additional symptom-medicine rules
        """
        self.rules = SYMPTOM_MEDICINE_RULES.copy()
        if custom_rules:
            self.rules.update(custom_rules)
        self._matched_symptoms = []
    
    def get_name(self) -> str:
        return "knowledge"
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptom keywords from text."""
        text_lower = text.lower()
        found_symptoms = []
        
        for symptom in self.rules.keys():
            if symptom in text_lower:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def _check_medicine_match(self, medicine: Dict, medicine_keywords: Set[str]) -> float:
        """
        Check how well a medicine matches the required keywords.
        
        Returns score between 0 and 1.
        """
        med_text = f"{medicine['name']} {medicine.get('description', '')}".lower()
        
        matched = 0
        total = len(medicine_keywords)
        
        for keyword in medicine_keywords:
            if keyword.lower() in med_text:
                matched += 1
        
        return matched / total if total > 0 else 0.0
    
    def recommend(
        self, 
        symptoms: str, 
        medicines: List[Dict]
    ) -> np.ndarray:
        """
        Generate recommendation scores using knowledge rules.
        
        Args:
            symptoms: Patient symptoms string
            medicines: List of medicine dictionaries
            
        Returns:
            np.ndarray: Rule-based scores for each medicine (0.0 to 1.0)
        """
        if not symptoms or not medicines:
            return np.zeros(len(medicines))
        
        try:
            # Extract symptoms from text
            self._matched_symptoms = self._extract_symptoms(symptoms)
            
            if not self._matched_symptoms:
                logger.info("No known symptoms found in text")
                return np.zeros(len(medicines))
            
            logger.info(f"Matched symptoms: {self._matched_symptoms}")
            
            # Collect all medicine keywords for matched symptoms
            all_keywords = set()
            for symptom in self._matched_symptoms:
                all_keywords.update(self.rules.get(symptom, set()))
            
            # Score each medicine based on keyword matches
            scores = []
            for medicine in medicines:
                score = self._check_medicine_match(medicine, all_keywords)
                scores.append(score)
            
            # Normalize scores
            scores = np.array(scores)
            max_score = scores.max()
            if max_score > 0:
                scores = scores / max_score
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in knowledge recommendation: {e}")
            return np.zeros(len(medicines))
    
    def get_feature_contributions(
        self, 
        symptoms: str, 
        medicine: Dict
    ) -> Dict[str, float]:
        """
        Get symptom contributions based on matched rules.
        """
        if not self._matched_symptoms:
            return {}
        
        med_text = f"{medicine['name']} {medicine.get('description', '')}".lower()
        
        contributions = {}
        for symptom in self._matched_symptoms:
            keywords = self.rules.get(symptom, set())
            # Check if any keyword for this symptom matches the medicine
            for keyword in keywords:
                if keyword.lower() in med_text:
                    contributions[symptom] = contributions.get(symptom, 0) + 0.2
                    break
        
        # Normalize
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: v/total for k, v in contributions.items()}
        
        return contributions
