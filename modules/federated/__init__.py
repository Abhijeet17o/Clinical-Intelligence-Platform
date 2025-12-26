"""
Federated Learning Package

This package provides federated learning for the Hybrid Recommender model,
with support for both simulation and real federated learning using Flower.
"""

from .simulation import FederatedSimulator
from .client_manager import ClientManager
from .fl_config import FLConfig

# Recommender FL (current implementation)
from .recommender_flower_client import RecommenderFlowerClient, create_recommender_client_fn
from .recommender_flower_server import RecommenderFLServerManager
from .recommender_trainer import RecommenderFLTrainer
from .recommender_data_loader import RecommenderFLDataLoader, RecommenderDataset

# Legacy Whisper FL (deprecated - kept for backward compatibility)
from .flower_client import WhisperFlowerClient, create_client_fn
from .flower_server import FLServerManager

__all__ = [
    # Current (Recommender)
    'RecommenderFlowerClient',
    'create_recommender_client_fn',
    'RecommenderFLServerManager',
    'RecommenderFLTrainer',
    'RecommenderFLDataLoader',
    'RecommenderDataset',
    # Common
    'FederatedSimulator',
    'ClientManager',
    'FLConfig',
    # Legacy (Deprecated)
    'WhisperFlowerClient',
    'create_client_fn',
    'FLServerManager',
]
