"""
TF-IDF Based Recommender

Uses TF-IDF vectorization with cosine similarity for keyword-based
matching between symptoms and medicine descriptions.
"""

import numpy as np
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

from .base_recommender import BaseRecommender

logger = logging.getLogger(__name__)


class TfidfRecommender(BaseRecommender):
    """
    Recommender based on TF-IDF vectorization.
    
    Good for keyword matching when specific medical terms should
    have high importance.
    """
    
    def __init__(self, ngram_range: tuple = (1, 2), max_features: int = 1000):
        """
        Initialize the TF-IDF recommender.
        
        Args:
            ngram_range: Range of n-grams to extract (default: unigrams and bigrams)
            max_features: Maximum vocabulary size
        """
        self.ngram_range = ngram_range
        self.max_features = max_features
        self._vectorizer = None
        self._feature_names = None
    
    def get_name(self) -> str:
        return "tfidf"
    
    def recommend(
        self, 
        symptoms: str, 
        medicines: List[Dict]
    ) -> np.ndarray:
        """
        Generate recommendation scores using TF-IDF similarity.
        
        Args:
            symptoms: Patient symptoms string
            medicines: List of medicine dictionaries
            
        Returns:
            np.ndarray: Similarity scores for each medicine (0.0 to 1.0)
        """
        if not symptoms or not medicines:
            return np.zeros(len(medicines))
        
        try:
            # Prepare medicine texts
            medicine_texts = [
                f"{med['name']} {med.get('description', '')}"
                for med in medicines
            ]
            
            # Combine all texts for fitting vectorizer
            all_texts = [symptoms] + medicine_texts
            
            # Create and fit TF-IDF vectorizer
            self._vectorizer = TfidfVectorizer(
                ngram_range=self.ngram_range,
                max_features=self.max_features,
                stop_words='english'
            )
            
            tfidf_matrix = self._vectorizer.fit_transform(all_texts)
            self._feature_names = self._vectorizer.get_feature_names_out()
            
            # Get symptom vector (first row)
            symptom_vector = tfidf_matrix[0:1]
            
            # Get medicine vectors (remaining rows)
            medicine_vectors = tfidf_matrix[1:]
            
            # Calculate cosine similarity
            similarities = cosine_similarity(symptom_vector, medicine_vectors)[0]
            
            # Ensure values are in [0, 1]
            scores = np.clip(similarities, 0.0, 1.0)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in TF-IDF recommendation: {e}")
            return np.zeros(len(medicines))
    
    def get_feature_contributions(
        self, 
        symptoms: str, 
        medicine: Dict
    ) -> Dict[str, float]:
        """
        Get keyword contributions to the recommendation.
        """
        if self._vectorizer is None or self._feature_names is None:
            return {}
        
        try:
            # Get TF-IDF values for symptoms
            symptom_vec = self._vectorizer.transform([symptoms]).toarray()[0]
            
            # Get non-zero features
            nonzero_indices = np.nonzero(symptom_vec)[0]
            
            contributions = {}
            for idx in nonzero_indices:
                feature = self._feature_names[idx]
                weight = float(symptom_vec[idx])
                contributions[feature] = weight
            
            # Normalize
            total = sum(contributions.values())
            if total > 0:
                contributions = {k: v/total for k, v in contributions.items()}
            
            return contributions
            
        except Exception:
            return {}
