"""
Semantic Similarity Recommender

Uses SentenceTransformer embeddings and cosine similarity to match
patient symptoms with medicine descriptions.
"""

import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import logging

from .base_recommender import BaseRecommender

logger = logging.getLogger(__name__)


class SemanticRecommender(BaseRecommender):
    """
    Recommender based on semantic similarity using sentence embeddings.
    
    Uses the all-MiniLM-L6-v2 model to encode symptoms and medicine descriptions,
    then calculates cosine similarity to rank medicines.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the semantic recommender.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
        """
        self.model_name = model_name
        self._model = None  # Lazy loading
        
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("✓ Model loaded successfully")
        return self._model
    
    def get_name(self) -> str:
        return "semantic"
    
    def recommend(
        self, 
        symptoms: str, 
        medicines: List[Dict]
    ) -> np.ndarray:
        """
        Generate recommendation scores using semantic similarity.
        
        Args:
            symptoms: Patient symptoms string
            medicines: List of medicine dictionaries
            
        Returns:
            np.ndarray: Similarity scores for each medicine (0.0 to 1.0)
        """
        if not symptoms or not medicines:
            return np.zeros(len(medicines))
        
        try:
            # Encode symptoms
            symptom_embedding = self.model.encode(symptoms, convert_to_tensor=False)
            
            # Prepare medicine texts
            medicine_texts = [
                f"{med['name']}: {med.get('description', '')}"
                for med in medicines
            ]
            
            # Encode all medicines
            medicine_embeddings = self.model.encode(medicine_texts, convert_to_tensor=False)
            
            # Calculate cosine similarity for each medicine
            scores = []
            for med_embedding in medicine_embeddings:
                # Cosine similarity = 1 - cosine distance
                similarity = 1 - cosine(symptom_embedding, med_embedding)
                # Clamp to [0, 1] range
                scores.append(max(0.0, min(1.0, similarity)))
            
            return np.array(scores)
            
        except Exception as e:
            logger.error(f"Error in semantic recommendation: {e}")
            return np.zeros(len(medicines))
    
    def get_feature_contributions(
        self, 
        symptoms: str, 
        medicine: Dict
    ) -> Dict[str, float]:
        """
        Estimate feature contributions based on word overlap with embeddings.
        """
        # Split symptoms into keywords
        symptom_words = symptoms.lower().split()
        med_text = f"{medicine['name']}: {medicine.get('description', '')}".lower()
        
        contributions = {}
        for word in symptom_words:
            if len(word) > 3:  # Skip short words
                if word in med_text:
                    contributions[word] = 0.3  # Higher if found in medicine text
                else:
                    contributions[word] = 0.1  # Lower if not found
        
        # Normalize
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: v/total for k, v in contributions.items()}
        
        return contributions
