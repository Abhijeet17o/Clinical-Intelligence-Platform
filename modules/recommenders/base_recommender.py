"""
Base Recommender Interface

Abstract base class that all recommendation models must implement.
Ensures consistent input/output formats for ensemble voting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
import numpy as np


class BaseRecommender(ABC):
    """
    Abstract base class for medicine recommendation models.
    
    All recommenders must implement the recommend() method which returns
    a score matrix that can be used in ensemble voting.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the unique identifier for this recommender.
        
        Returns:
            str: Name of the recommender (e.g., 'semantic', 'tfidf', 'knowledge')
        """
        pass
    
    @abstractmethod
    def recommend(
        self, 
        symptoms: str, 
        medicines: List[Dict]
    ) -> np.ndarray:
        """
        Generate recommendation scores for each medicine based on symptoms.
        
        Args:
            symptoms: String describing patient symptoms extracted from transcript
            medicines: List of medicine dictionaries from database, each containing:
                       - name: str
                       - description: str
                       - stock_level: int
                       - prescription_frequency: int
        
        Returns:
            np.ndarray: 1D array of scores (0.0 to 1.0) for each medicine,
                        in the same order as the input medicines list.
                        Higher scores indicate better matches.
        """
        pass
    
    def get_feature_contributions(
        self, 
        symptoms: str, 
        medicine: Dict
    ) -> Dict[str, float]:
        """
        Returns feature contributions for explainability.
        Override in subclasses that support feature-level explanations.
        
        Args:
            symptoms: Patient symptoms string
            medicine: Single medicine dictionary
            
        Returns:
            Dict mapping feature names to their contribution weights
        """
        return {}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.get_name()}')"
