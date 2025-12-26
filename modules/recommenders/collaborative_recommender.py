"""
Collaborative Filtering Recommender

Uses historical prescription data to recommend medicines based on
what was prescribed to similar patients in the past.
"""

import numpy as np
from typing import List, Dict, Optional
import logging
import json

from .base_recommender import BaseRecommender

logger = logging.getLogger(__name__)


class CollaborativeRecommender(BaseRecommender):
    """
    Recommender based on collaborative filtering using prescription history.
    
    Analyzes past prescriptions for similar symptoms and recommends
    medicines that were frequently prescribed together.
    """
    
    def __init__(self, db_connection=None, history_weight: float = 0.7):
        """
        Initialize the collaborative recommender.
        
        Args:
            db_connection: Database connection for fetching prescription history
            history_weight: Weight for historical frequency vs recency (0-1)
        """
        self.db = db_connection
        self.history_weight = history_weight
        self._prescription_cache = {}
    
    def get_name(self) -> str:
        return "collaborative"
    
    def set_database(self, db_connection):
        """Set the database connection for fetching history."""
        self.db = db_connection
        self._prescription_cache = {}
    
    def _load_prescription_history(self) -> List[Dict]:
        """Load all prescription history from database."""
        if not self.db:
            return []
        
        try:
            patients = self.db.get_all_patients()
            all_prescriptions = []
            
            for patient in patients:
                ehr_data = patient.get('ehr_data', '{}')
                if isinstance(ehr_data, str):
                    ehr_data = json.loads(ehr_data) if ehr_data else {}
                
                prescriptions = ehr_data.get('prescriptions', [])
                symptoms = ehr_data.get('symptoms', [])
                
                for prescription in prescriptions:
                    all_prescriptions.append({
                        'symptoms': symptoms,
                        'medicines': prescription.get('medicines', []),
                        'date': prescription.get('date', '')
                    })
            
            return all_prescriptions
            
        except Exception as e:
            logger.error(f"Error loading prescription history: {e}")
            return []
    
    def _find_similar_prescriptions(
        self, 
        symptoms: str, 
        history: List[Dict]
    ) -> Dict[str, float]:
        """
        Find medicines from prescriptions with similar symptoms.
        
        Returns a dict of medicine names to their frequency scores.
        """
        symptom_words = set(symptoms.lower().split())
        medicine_scores = {}
        
        for prescription in history:
            hist_symptoms = prescription.get('symptoms', [])
            
            # Calculate symptom overlap
            if isinstance(hist_symptoms, list):
                hist_symptom_words = set(
                    word.lower() 
                    for s in hist_symptoms 
                    for word in str(s).split()
                )
            else:
                hist_symptom_words = set(str(hist_symptoms).lower().split())
            
            # Jaccard similarity for symptoms
            intersection = symptom_words & hist_symptom_words
            union = symptom_words | hist_symptom_words
            
            if not union:
                continue
            
            similarity = len(intersection) / len(union)
            
            if similarity > 0.1:  # Threshold for relevance
                # Add medicine scores weighted by symptom similarity
                medicines = prescription.get('medicines', [])
                for med in medicines:
                    med_name = med.get('name', '') if isinstance(med, dict) else str(med)
                    if med_name:
                        current = medicine_scores.get(med_name, 0)
                        medicine_scores[med_name] = current + similarity
        
        return medicine_scores
    
    def recommend(
        self, 
        symptoms: str, 
        medicines: List[Dict]
    ) -> np.ndarray:
        """
        Generate recommendation scores using collaborative filtering.
        
        Args:
            symptoms: Patient symptoms string
            medicines: List of medicine dictionaries
            
        Returns:
            np.ndarray: Collaborative scores for each medicine (0.0 to 1.0)
        """
        if not symptoms or not medicines:
            return np.zeros(len(medicines))
        
        try:
            # Load prescription history
            history = self._load_prescription_history()
            
            if not history:
                # Fall back to prescription frequency if no history
                logger.info("No prescription history, using frequency")
                frequencies = np.array([
                    med.get('prescription_frequency', 0) 
                    for med in medicines
                ])
                max_freq = frequencies.max()
                if max_freq > 0:
                    return frequencies / max_freq
                return np.zeros(len(medicines))
            
            # Find similar prescriptions
            medicine_scores = self._find_similar_prescriptions(symptoms, history)
            
            # Also consider prescription frequency from database
            for med in medicines:
                name = med['name']
                freq = med.get('prescription_frequency', 0)
                if name in medicine_scores:
                    medicine_scores[name] += freq * 0.1  # Add frequency boost
            
            # Map scores to medicine list
            scores = []
            for med in medicines:
                score = medicine_scores.get(med['name'], 0)
                scores.append(score)
            
            scores = np.array(scores)
            
            # Normalize
            max_score = scores.max()
            if max_score > 0:
                scores = scores / max_score
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in collaborative recommendation: {e}")
            return np.zeros(len(medicines))
    
    def get_feature_contributions(
        self, 
        symptoms: str, 
        medicine: Dict
    ) -> Dict[str, float]:
        """
        Get contributions based on historical patterns.
        """
        return {
            "prescription_history": 0.6,
            "similar_patients": 0.4
        }
