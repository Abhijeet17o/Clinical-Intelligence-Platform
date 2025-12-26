"""
Federated Learning Configuration

Configuration parameters for federated learning (both simulation and real FL).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class FLConfig:
    """Configuration for Federated Learning."""
    
    # Server settings
    num_rounds: int = 5
    min_clients: int = 2
    fraction_fit: float = 0.5  # Fraction of clients to use per round
    server_address: str = "0.0.0.0:8080"  # Flower server address
    
    # Client settings
    local_epochs: int = 1
    batch_size: int = 32
    learning_rate: float = 0.001
    max_grad_norm: float = 1.0  # Gradient clipping
    
    # Model settings (for recommender)
    model_type: str = "recommender"  # "recommender" - only recommender is supported
    checkpoint_dir: Optional[str] = "data/fl_checkpoints"  # Model checkpoint directory
    
    # Data settings
    data_dir: str = "data/sessions"  # Root directory for training data
    data_split: str = "iid"  # iid or non-iid
    data_seed: Optional[int] = None  # Random seed for data splitting
    db_path: Optional[str] = "pharmacy.db"  # Database path for prescription data
    
    # Deployment settings
    deployment_mode: str = "hybrid"  # "local", "distributed", or "hybrid"
    num_simulated_clients: int = 3  # For local/simulation mode
    use_simulation: bool = False  # Use simulation mode instead of real FL
    
    # Flower-specific settings
    fraction_evaluate: float = 0.5  # Fraction of clients for evaluation
    min_evaluate_clients: int = 2  # Minimum clients for evaluation
    min_available_clients: int = 2  # Minimum available clients before starting
    
    # Client management
    heartbeat_timeout: int = 60  # Seconds before considering client offline
    max_client_failures: int = 3  # Max failures before marking client as failed
    
    # Security settings
    enable_auth: bool = False  # Enable client authentication
    auth_token: Optional[str] = None  # Authentication token
    enable_encryption: bool = False  # Enable model weight encryption
    ssl_cert_path: Optional[str] = None  # Path to SSL certificate
    
    # Monitoring and logging
    verbose: bool = True
    log_interval: int = 1
    results_file: str = "data/fl_results.json"  # Results output file
    save_checkpoints: bool = True  # Save model checkpoints
    
    # Device settings
    device: str = "auto"  # "auto", "cpu", or "cuda"
    
    # Additional metadata
    metadata: Dict = field(default_factory=dict)


# Default configurations for different scenarios
DEMO_CONFIG = FLConfig(
    num_rounds=3,
    num_simulated_clients=3,
    local_epochs=1,
    verbose=True,
    use_simulation=True
)

PRODUCTION_CONFIG = FLConfig(
    num_rounds=10,
    num_simulated_clients=5,
    local_epochs=3,
    verbose=False,
    use_simulation=False,
    enable_auth=True,
    save_checkpoints=True
)

# Local development config (multi-process on same machine)
LOCAL_CONFIG = FLConfig(
    num_rounds=5,
    num_simulated_clients=3,
    local_epochs=2,
    deployment_mode="local",
    use_simulation=False,
    verbose=True
)

# Distributed production config
DISTRIBUTED_CONFIG = FLConfig(
    num_rounds=20,
    min_clients=3,
    local_epochs=3,
    deployment_mode="distributed",
    use_simulation=False,
    enable_auth=True,
    enable_encryption=True,
    save_checkpoints=True,
    verbose=False
)
