"""
Federated Learning Trainer for Hybrid Recommender

Handles training and updating of ensemble weights and recommender models
in a federated learning setting.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import os

from .recommender_data_loader import RecommenderDataset
from ..ensemble_engine import EnsembleRecommender

logger = logging.getLogger(__name__)


class RecommenderFLTrainer:
    """
    Trainer for Hybrid Recommender in federated learning.
    
    Trains ensemble weights and optionally fine-tunes individual models.
    """
    
    def __init__(
        self,
        db_connection=None,
        checkpoint_dir: Optional[str] = None
    ):
        """
        Initialize recommender trainer.
        
        Args:
            db_connection: Database connection for collaborative filtering
            checkpoint_dir: Directory to save checkpoints
        """
        self.db = db_connection
        self.checkpoint_dir = checkpoint_dir
        
        # Initialize ensemble recommender
        self.ensemble = EnsembleRecommender(
            db_connection=db_connection,
            use_learnable_weights=True,
            parallel_execution=True
        )
        
        # Training history
        self.training_history: List[Dict] = []
        
        logger.info("Initialized RecommenderFLTrainer")
    
    def get_model_parameters(self) -> List[np.ndarray]:
        """
        Get model parameters as NumPy arrays (for Flower).
        
        Returns ensemble weights as parameters.
        """
        weights = self.ensemble.get_model_weights()
        # Convert weights dict to array
        weight_array = np.array([
            weights.get("semantic", 0.25),
            weights.get("tfidf", 0.25),
            weights.get("knowledge", 0.25),
            weights.get("collaborative", 0.25)
        ])
        return [weight_array]
    
    def set_model_parameters(self, parameters: List[np.ndarray]):
        """
        Set model parameters from NumPy arrays (from Flower).
        
        Args:
            parameters: List of parameter arrays (ensemble weights)
        """
        if len(parameters) > 0:
            weight_array = parameters[0]
            # Ensure we have 4 weights
            if len(weight_array) >= 4:
                weights = {
                    "semantic": float(weight_array[0]),
                    "tfidf": float(weight_array[1]),
                    "knowledge": float(weight_array[2]),
                    "collaborative": float(weight_array[3])
                }
                # Normalize
                total = sum(weights.values())
                if total > 0:
                    weights = {k: v/total for k, v in weights.items()}
                
                self.ensemble.set_model_weights(weights)
                logger.info(f"Updated ensemble weights: {weights}")
    
    def train_epoch(
        self,
        dataset: RecommenderDataset,
        learning_rate: float = 0.1,
        all_medicines: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Train for one epoch using prescription feedback.
        
        Args:
            dataset: RecommenderDataset with symptoms -> medicines pairs
            learning_rate: Learning rate for weight updates
            all_medicines: List of all available medicines (for recommendations)
        
        Returns:
            Dict with training metrics
        """
        if all_medicines is None:
            if self.db:
                all_medicines = self.db.get_all_medicines()
            else:
                logger.warning("No medicines available for training")
                return {"loss": 1.0, "accuracy": 0.0, "num_samples": 0}
        
        total_loss = 0.0
        correct_predictions = 0
        total_samples = 0
        
        for sample in dataset.data_pairs:
            symptoms, true_medicines = sample
            
            try:
                # Get recommendations from ensemble
                recommendations = self.ensemble.get_recommendations(
                    symptoms=symptoms,
                    medicines=all_medicines,
                    top_n=len(true_medicines) + 5  # Get more than needed
                )
                
                if not recommendations:
                    continue
                
                # Extract recommended medicine names
                recommended_names = [rec['name'] for rec in recommendations]
                
                # Calculate metrics
                # Precision: How many recommended medicines were actually prescribed
                true_set = set(true_medicines)
                recommended_set = set(recommended_names[:len(true_medicines)])
                
                if len(true_set) > 0:
                    precision = len(true_set & recommended_set) / len(true_set)
                    correct_predictions += len(true_set & recommended_set)
                else:
                    precision = 0.0
                
                # Loss: 1 - precision (lower is better)
                loss = 1.0 - precision
                total_loss += loss
                total_samples += 1
                
                # Update weights based on feedback (simulated learning)
                # If top recommendation matches, boost that model's weight
                if recommendations and recommendations[0]['name'] in true_set:
                    # This medicine was correctly recommended
                    # Update weights to favor models that contributed
                    self.ensemble.update_weights_from_feedback(
                        selected_medicine=recommendations[0]['name'],
                        learning_rate=learning_rate * 0.1  # Smaller update per sample
                    )
            
            except Exception as e:
                logger.warning(f"Error processing sample: {e}")
                continue
        
        avg_loss = total_loss / max(total_samples, 1)
        accuracy = correct_predictions / max(total_samples, 1) if total_samples > 0 else 0.0
        
        metrics = {
            "loss": avg_loss,
            "accuracy": accuracy,
            "precision": accuracy,  # Using accuracy as precision metric
            "num_samples": total_samples
        }
        
        self.training_history.append(metrics)
        
        return metrics
    
    def evaluate(
        self,
        dataset: RecommenderDataset,
        all_medicines: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Evaluate model on validation/test data.
        
        Args:
            dataset: RecommenderDataset
            all_medicines: List of all available medicines
        
        Returns:
            Dict with evaluation metrics
        """
        if all_medicines is None:
            if self.db:
                all_medicines = self.db.get_all_medicines()
            else:
                return {"loss": 1.0, "accuracy": 0.0, "num_samples": 0}
        
        total_loss = 0.0
        correct_predictions = 0
        total_samples = 0
        
        for sample in dataset.data_pairs:
            symptoms, true_medicines = sample
            
            try:
                recommendations = self.ensemble.get_recommendations(
                    symptoms=symptoms,
                    medicines=all_medicines,
                    top_n=len(true_medicines) + 5
                )
                
                if not recommendations:
                    continue
                
                recommended_names = [rec['name'] for rec in recommendations]
                true_set = set(true_medicines)
                recommended_set = set(recommended_names[:len(true_medicines)])
                
                if len(true_set) > 0:
                    precision = len(true_set & recommended_set) / len(true_set)
                    correct_predictions += len(true_set & recommended_set)
                else:
                    precision = 0.0
                
                loss = 1.0 - precision
                total_loss += loss
                total_samples += 1
            
            except Exception as e:
                logger.warning(f"Error evaluating sample: {e}")
                continue
        
        avg_loss = total_loss / max(total_samples, 1)
        accuracy = correct_predictions / max(total_samples, 1) if total_samples > 0 else 0.0
        
        return {
            "loss": avg_loss,
            "accuracy": accuracy,
            "precision": accuracy,
            "num_samples": total_samples
        }
    
    def save_checkpoint(
        self,
        round_num: int,
        metrics: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Save model checkpoint.
        
        Args:
            round_num: Federated learning round number
            metrics: Optional metrics to save
        
        Returns:
            Path to saved checkpoint
        """
        if self.checkpoint_dir is None:
            return None
        
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        checkpoint_path = os.path.join(
            self.checkpoint_dir,
            f"recommender_ensemble_round_{round_num}.json"
        )
        
        checkpoint = {
            "weights": self.ensemble.get_model_weights(),
            "round_num": round_num,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics or {}
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.info(f"Saved checkpoint to {checkpoint_path}")
        
        return checkpoint_path
    
    def load_checkpoint(self, checkpoint_path: str):
        """
        Load model checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
        """
        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)
        
        self.ensemble.set_model_weights(checkpoint["weights"])
        logger.info(f"Loaded checkpoint from {checkpoint_path}")

