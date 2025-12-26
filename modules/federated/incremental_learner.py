"""
Incremental Federated Learning Service

Learns from individual prescription events automatically.
Each prescription save triggers a learning update.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from ..ensemble_engine import EnsembleRecommender

logger = logging.getLogger(__name__)


class IncrementalLearner:
    """
    Handles incremental learning from individual prescription events.
    
    Each time a doctor saves a prescription, this learns from:
    - Symptoms (from transcript)
    - Recommended medicines (from ensemble)
    - Doctor's actual choice (from prescription)
    """
    
    def __init__(
        self,
        ensemble: Optional[EnsembleRecommender] = None,
        learning_rate: float = 0.1
    ):
        """
        Initialize incremental learner.
        
        Args:
            ensemble: EnsembleRecommender instance (creates new if None)
            learning_rate: Learning rate for weight updates
        """
        if ensemble is None:
            self.ensemble = EnsembleRecommender(use_learnable_weights=True)
        else:
            self.ensemble = ensemble
        
        self.learning_rate = learning_rate
        self.learning_count = 0
        
        logger.info("Initialized IncrementalLearner")
    
    def learn_from_prescription(
        self,
        symptoms: str,
        recommended_medicines: List[str],
        selected_medicine: str,
        all_medicines: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Learn from a single prescription event.
        
        Args:
            symptoms: Patient symptoms text
            recommended_medicines: List of medicine names that were recommended
            selected_medicine: Medicine name that doctor actually chose
            all_medicines: Full list of medicines (for getting recommendations if needed)
        
        Returns:
            Dict with learning results:
            - success: bool
            - weights_before: dict of weights before update
            - weights_after: dict of weights after update
            - weight_changes: dict of weight deltas
            - learning_timestamp: ISO timestamp
        """
        try:
            # Get current weights
            weights_before = self.ensemble.get_model_weights().copy()
            
            # Ensure we have the vote matrix from last recommendations
            # If not, we need to regenerate recommendations
            if self.ensemble.last_vote_matrix is None or self.ensemble.last_medicine_names is None:
                logger.warning("No vote matrix available, regenerating recommendations")
                if all_medicines:
                    # Regenerate to get vote matrix
                    recommendations = self.ensemble.get_recommendations(
                        symptoms=symptoms,
                        medicines=all_medicines,
                        top_n=len(recommended_medicines) + 5
                    )
                else:
                    logger.warning("Cannot learn: no medicines available and no vote matrix")
                    return {
                        'success': False,
                        'error': 'No vote matrix or medicines available'
                    }
            
            # Update weights based on doctor's selection
            self.ensemble.update_weights_from_feedback(
                selected_medicine=selected_medicine,
                learning_rate=self.learning_rate
            )
            
            # Get updated weights
            weights_after = self.ensemble.get_model_weights().copy()
            
            # Calculate weight changes
            weight_changes = {
                model: weights_after[model] - weights_before[model]
                for model in weights_before.keys()
            }
            
            self.learning_count += 1
            
            result = {
                'success': True,
                'weights_before': weights_before,
                'weights_after': weights_after,
                'weight_changes': weight_changes,
                'learning_timestamp': datetime.now().isoformat(),
                'learning_count': self.learning_count,
                'selected_medicine': selected_medicine,
                'symptoms': symptoms[:100] if len(symptoms) > 100 else symptoms  # Truncate for storage
            }
            
            logger.info(
                f"Learned from prescription #{self.learning_count}: "
                f"{selected_medicine} for symptoms: {symptoms[:50]}..."
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error in incremental learning: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_learning_count(self) -> int:
        """Get total number of learning events."""
        return self.learning_count
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current ensemble weights."""
        return self.ensemble.get_model_weights()

