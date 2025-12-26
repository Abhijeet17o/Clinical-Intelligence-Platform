"""
Federated Learning Configuration

Configuration parameters for federated learning simulation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FLConfig:
    """Configuration for Federated Learning simulation."""
    
    # Server settings
    num_rounds: int = 5
    min_clients: int = 2
    fraction_fit: float = 0.5  # Fraction of clients to use per round
    
    # Client settings
    local_epochs: int = 1
    batch_size: int = 32
    learning_rate: float = 0.001
    
    # Model settings
    whisper_model: str = "base"  # tiny, base, small, medium, large
    freeze_encoder: bool = True  # Freeze Whisper encoder, train only fine-tuning layers
    
    # Simulation settings
    num_simulated_clients: int = 3
    data_split: str = "iid"  # iid or non-iid
    
    # Logging
    verbose: bool = True
    log_interval: int = 1


# Default configurations for different scenarios
DEMO_CONFIG = FLConfig(
    num_rounds=3,
    num_simulated_clients=3,
    local_epochs=1,
    verbose=True
)

PRODUCTION_CONFIG = FLConfig(
    num_rounds=10,
    num_simulated_clients=5,
    local_epochs=3,
    verbose=False
)
