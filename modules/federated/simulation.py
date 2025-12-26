"""
Federated Learning Simulation

Simulates federated learning for Whisper model fine-tuning.
This is a demonstration/prototype implementation that shows
the key FL concepts without requiring actual distributed setup.

Key Concepts Demonstrated:
1. Multiple simulated hospital clients
2. Local model training on private data
3. FedAvg aggregation on the server
4. Privacy-preserving model updates (only weights shared, not data)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
import logging
import json
import os
from datetime import datetime
from dataclasses import asdict

from .fl_config import FLConfig, DEMO_CONFIG

logger = logging.getLogger(__name__)


class SimulatedClient:
    """
    Simulates a federated learning client (e.g., a hospital).
    
    In a real FL setup, this would be a separate machine/process.
    For demonstration, we simulate local training with dummy metrics.
    """
    
    def __init__(self, client_id: str, data_size: int = 100):
        """
        Initialize a simulated client.
        
        Args:
            client_id: Unique identifier (e.g., "hospital_A")
            data_size: Simulated number of local training samples
        """
        self.client_id = client_id
        self.data_size = data_size
        self.model_version = 0
        self.local_metrics = []
    
    def get_properties(self) -> Dict:
        """Return client properties for server."""
        return {
            "client_id": self.client_id,
            "data_size": self.data_size,
            "model_version": self.model_version
        }
    
    def receive_global_model(self, global_weights: np.ndarray, version: int):
        """Receive global model weights from server."""
        self.model_version = version
        self._local_weights = global_weights.copy()
        logger.info(f"[{self.client_id}] Received global model v{version}")
    
    def local_train(self, epochs: int = 1, learning_rate: float = 0.001) -> Dict:
        """
        Simulate local training on private data.
        
        In real FL, this would:
        1. Load local (private) data
        2. Train the model for specified epochs
        3. Return updated weights
        
        For simulation, we add noise to weights to simulate training.
        """
        # Simulate training by adding small random updates
        noise = np.random.randn(*self._local_weights.shape) * learning_rate
        self._local_weights += noise
        
        # Simulate metrics (would be actual loss/accuracy in real implementation)
        simulated_loss = np.random.uniform(0.1, 0.5)
        simulated_wer = np.random.uniform(0.1, 0.3)  # Word Error Rate
        
        metrics = {
            "client_id": self.client_id,
            "loss": round(simulated_loss, 4),
            "wer": round(simulated_wer, 4),
            "samples_used": self.data_size,
            "epochs": epochs
        }
        
        self.local_metrics.append(metrics)
        logger.info(f"[{self.client_id}] Local training complete. Loss: {simulated_loss:.4f}")
        
        return metrics
    
    def get_model_update(self) -> Tuple[np.ndarray, int]:
        """
        Return model weights and number of samples.
        
        Returns:
            Tuple of (weights, num_samples) for weighted averaging
        """
        return self._local_weights, self.data_size


class FederatedSimulator:
    """
    Simulates federated learning for Whisper transcription model.
    
    This demonstrates the FL workflow:
    1. Server initializes global model
    2. Server selects subset of clients each round
    3. Clients train locally on their private data
    4. Server aggregates updates using FedAvg
    5. Repeat for specified number of rounds
    
    Usage:
        simulator = FederatedSimulator(config=DEMO_CONFIG)
        results = simulator.run_simulation()
        print(simulator.get_metrics_summary())
    """
    
    # File to store simulation results
    RESULTS_FILE = "data/fl_simulation_results.json"
    
    def __init__(self, config: FLConfig = None):
        """
        Initialize the federated learning simulator.
        
        Args:
            config: FL configuration (uses DEMO_CONFIG if not provided)
        """
        self.config = config or DEMO_CONFIG
        self.clients: List[SimulatedClient] = []
        self.global_weights: Optional[np.ndarray] = None
        self.round_metrics: List[Dict] = []
        self.current_round = 0
        
        # Initialize simulated clients
        self._create_simulated_clients()
        
        # Initialize global model (simulated as weight vector)
        self._initialize_global_model()
        
        logger.info(f"Initialized FederatedSimulator with {len(self.clients)} clients")
    
    def _create_simulated_clients(self):
        """Create simulated hospital clients."""
        hospital_names = [
            "Hospital_A", "Hospital_B", "Hospital_C", 
            "Hospital_D", "Hospital_E"
        ]
        
        for i in range(self.config.num_simulated_clients):
            client_id = hospital_names[i % len(hospital_names)]
            # Simulate varying data sizes across hospitals
            data_size = np.random.randint(50, 200)
            self.clients.append(SimulatedClient(client_id, data_size))
    
    def _initialize_global_model(self):
        """Initialize global model weights."""
        # Simulated weight vector (in reality, this would be Whisper parameters)
        # We use 1000 dimensions to represent model parameters
        self.global_weights = np.random.randn(1000) * 0.01
        logger.info("Initialized global model weights")
    
    def _select_clients(self) -> List[SimulatedClient]:
        """Select clients for this round based on fraction_fit."""
        num_selected = max(
            self.config.min_clients,
            int(len(self.clients) * self.config.fraction_fit)
        )
        selected = np.random.choice(
            self.clients, 
            size=min(num_selected, len(self.clients)),
            replace=False
        ).tolist()
        return selected
    
    def _fedavg_aggregate(
        self, 
        client_updates: List[Tuple[np.ndarray, int]]
    ) -> np.ndarray:
        """
        Aggregate client updates using Federated Averaging.
        
        FedAvg weights each client's contribution by their sample count:
        new_weights = sum(client_weights * client_samples) / total_samples
        """
        total_samples = sum(samples for _, samples in client_updates)
        
        if total_samples == 0:
            return self.global_weights
        
        # Weighted average
        aggregated = np.zeros_like(self.global_weights)
        for weights, samples in client_updates:
            weight_factor = samples / total_samples
            aggregated += weights * weight_factor
        
        return aggregated
    
    def run_round(self) -> Dict:
        """
        Execute one round of federated learning.
        
        Returns:
            Dict with round metrics
        """
        self.current_round += 1
        round_start = datetime.now()
        
        if self.config.verbose:
            logger.info(f"\n{'='*50}")
            logger.info(f"ROUND {self.current_round}/{self.config.num_rounds}")
            logger.info(f"{'='*50}")
        
        # Step 1: Select clients
        selected_clients = self._select_clients()
        client_ids = [c.client_id for c in selected_clients]
        logger.info(f"Selected clients: {client_ids}")
        
        # Step 2: Distribute global model to selected clients
        for client in selected_clients:
            client.receive_global_model(self.global_weights, self.current_round)
        
        # Step 3: Local training on each client
        client_metrics = []
        client_updates = []
        
        for client in selected_clients:
            # Local training
            metrics = client.local_train(
                epochs=self.config.local_epochs,
                learning_rate=self.config.learning_rate
            )
            client_metrics.append(metrics)
            
            # Get model update
            update = client.get_model_update()
            client_updates.append(update)
        
        # Step 4: Aggregate updates using FedAvg
        self.global_weights = self._fedavg_aggregate(client_updates)
        
        # Calculate round metrics
        avg_loss = np.mean([m['loss'] for m in client_metrics])
        avg_wer = np.mean([m['wer'] for m in client_metrics])
        
        round_metrics = {
            "round": self.current_round,
            "num_clients": len(selected_clients),
            "participating_clients": client_ids,
            "avg_loss": round(avg_loss, 4),
            "avg_wer": round(avg_wer, 4),
            "duration_ms": (datetime.now() - round_start).total_seconds() * 1000,
            "client_metrics": client_metrics
        }
        
        self.round_metrics.append(round_metrics)
        
        if self.config.verbose:
            logger.info(f"Round {self.current_round} complete. "
                       f"Avg Loss: {avg_loss:.4f}, Avg WER: {avg_wer:.4f}")
        
        return round_metrics
    
    def run_simulation(self) -> Dict:
        """
        Run complete federated learning simulation.
        
        Returns:
            Dict with complete simulation results
        """
        start_time = datetime.now()
        logger.info("\n" + "="*60)
        logger.info("FEDERATED LEARNING SIMULATION STARTED")
        logger.info(f"Configuration: {self.config.num_rounds} rounds, "
                   f"{self.config.num_simulated_clients} clients")
        logger.info("="*60 + "\n")
        
        # Run all rounds
        for _ in range(self.config.num_rounds):
            self.run_round()
        
        # Compile results
        results = {
            "simulation_complete": True,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "config": asdict(self.config),
            "num_clients": len(self.clients),
            "total_rounds": self.config.num_rounds,
            "rounds": self.round_metrics,
            "final_metrics": {
                "avg_loss": round(np.mean([r['avg_loss'] for r in self.round_metrics]), 4),
                "avg_wer": round(np.mean([r['avg_wer'] for r in self.round_metrics]), 4),
                "loss_improvement": round(
                    self.round_metrics[0]['avg_loss'] - self.round_metrics[-1]['avg_loss'], 4
                ) if len(self.round_metrics) > 1 else 0
            }
        }
        
        # Save results
        self._save_results(results)
        
        logger.info("\n" + "="*60)
        logger.info("FEDERATED LEARNING SIMULATION COMPLETE")
        logger.info(f"Total duration: {results['duration_seconds']:.2f} seconds")
        logger.info(f"Final Avg Loss: {results['final_metrics']['avg_loss']:.4f}")
        logger.info("="*60 + "\n")
        
        return results
    
    def _save_results(self, results: Dict):
        """Save simulation results to file."""
        try:
            os.makedirs(os.path.dirname(self.RESULTS_FILE), exist_ok=True)
            with open(self.RESULTS_FILE, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {self.RESULTS_FILE}")
        except Exception as e:
            logger.error(f"Could not save results: {e}")
    
    def get_metrics_summary(self) -> Dict:
        """
        Get summary of metrics for display.
        
        Returns:
            Dict suitable for display in UI
        """
        if not self.round_metrics:
            return {"status": "No simulation run yet"}
        
        return {
            "status": "complete",
            "total_rounds": len(self.round_metrics),
            "total_clients": len(self.clients),
            "rounds_data": [
                {
                    "round": r["round"],
                    "clients": r["num_clients"],
                    "loss": r["avg_loss"],
                    "wer": r["avg_wer"]
                }
                for r in self.round_metrics
            ],
            "improvement": {
                "loss_delta": round(
                    self.round_metrics[0]['avg_loss'] - self.round_metrics[-1]['avg_loss'], 4
                ) if len(self.round_metrics) > 1 else 0,
                "wer_delta": round(
                    self.round_metrics[0]['avg_wer'] - self.round_metrics[-1]['avg_wer'], 4
                ) if len(self.round_metrics) > 1 else 0
            }
        }
    
    def get_client_details(self) -> List[Dict]:
        """Get details about all simulated clients."""
        return [client.get_properties() for client in self.clients]


# Demo function for standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("FEDERATED LEARNING DEMO")
    print("="*60)
    
    # Run simulation with demo config
    simulator = FederatedSimulator(config=DEMO_CONFIG)
    results = simulator.run_simulation()
    
    print("\nClient Details:")
    for client in simulator.get_client_details():
        print(f"  - {client['client_id']}: {client['data_size']} samples")
    
    print("\nMetrics Summary:")
    summary = simulator.get_metrics_summary()
    for round_data in summary['rounds_data']:
        print(f"  Round {round_data['round']}: "
              f"Loss={round_data['loss']:.4f}, WER={round_data['wer']:.4f}")
    
    print(f"\nImprovement: Loss {summary['improvement']['loss_delta']:.4f}, "
          f"WER {summary['improvement']['wer_delta']:.4f}")
