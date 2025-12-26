"""
Flower Server Implementation for Recommender System

Sets up and manages Flower server for federated learning of Hybrid Recommender.
"""

import logging
import threading
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
import json
import os
from flwr.server import Server, ServerConfig
from flwr.server.strategy import FedAvg
from flwr.server.strategy.aggregate import weighted_loss_avg
from flwr.common import Parameters, FitRes, EvaluateRes
import numpy as np

from .fl_config import FLConfig
from .utils import retry, safe_execute, GracefulDegradation, generate_auth_token

logger = logging.getLogger(__name__)


class RecommenderFLServerManager:
    """
    Manages Flower server for recommender federated learning.
    """
    
    def __init__(
        self,
        config: FLConfig,
        client_fn: Optional[Callable] = None,
        results_file: str = "data/fl_recommender_results.json"
    ):
        """
        Initialize FL server manager for recommender.
        
        Args:
            config: FL configuration
            client_fn: Function to create clients (for simulation mode)
            results_file: Path to save results
        """
        self.config = config
        self.client_fn = client_fn
        self.results_file = results_file
        self.server: Optional[Server] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.round_metrics: List[Dict] = []
        self.current_round = 0
        self.monitoring_callbacks: List[Callable] = []
        
        # Security: Generate auth token if enabled but not provided
        if config.enable_auth and not config.auth_token:
            self.auth_token = generate_auth_token()
            logger.info("Generated authentication token for server")
        else:
            self.auth_token = config.auth_token
        
        # Create results directory
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    def create_strategy(self) -> FedAvg:
        """
        Create FedAvg strategy with configuration for recommender.
        
        Returns:
            FedAvg strategy instance
        """
        # Define fit/evaluate metrics aggregation
        def fit_metrics_aggregation_fn(results: List[Tuple[int, FitRes]]) -> Dict:
            """Aggregate fit metrics across clients."""
            if not results:
                return {}
            
            # Aggregate losses and accuracies
            losses = [res.metrics.get("loss", 1.0) for _, res in results]
            accuracies = [res.metrics.get("accuracy", 0.0) for _, res in results]
            precisions = [res.metrics.get("precision", 0.0) for _, res in results]
            num_samples = [res.num_examples for _, res in results]
            
            # Weighted average
            total_samples = sum(num_samples)
            if total_samples > 0:
                avg_loss = sum(l * n for l, n in zip(losses, num_samples)) / total_samples
                avg_accuracy = sum(a * n for a, n in zip(accuracies, num_samples)) / total_samples
                avg_precision = sum(p * n for p, n in zip(precisions, num_samples)) / total_samples
            else:
                avg_loss = np.mean(losses) if losses else 1.0
                avg_accuracy = np.mean(accuracies) if accuracies else 0.0
                avg_precision = np.mean(precisions) if precisions else 0.0
            
            return {
                "loss": float(avg_loss),
                "accuracy": float(avg_accuracy),
                "precision": float(avg_precision),
                "num_clients": len(results)
            }
        
        def evaluate_metrics_aggregation_fn(results: List[Tuple[int, EvaluateRes]]) -> Dict:
            """Aggregate evaluation metrics across clients."""
            if not results:
                return {}
            
            losses = [res.loss for _, res in results]
            accuracies = [res.metrics.get("accuracy", 0.0) for _, res in results]
            precisions = [res.metrics.get("precision", 0.0) for _, res in results]
            num_samples = [res.num_examples for _, res in results]
            
            total_samples = sum(num_samples)
            if total_samples > 0:
                avg_loss = weighted_loss_avg(results)
                avg_accuracy = sum(a * n for a, n in zip(accuracies, num_samples)) / total_samples
                avg_precision = sum(p * n for p, n in zip(precisions, num_samples)) / total_samples
            else:
                avg_loss = np.mean(losses) if losses else 1.0
                avg_accuracy = np.mean(accuracies) if accuracies else 0.0
                avg_precision = np.mean(precisions) if precisions else 0.0
            
            return {
                "loss": float(avg_loss),
                "accuracy": float(avg_accuracy),
                "precision": float(avg_precision),
                "num_clients": len(results)
            }
        
        strategy = FedAvg(
            fraction_fit=self.config.fraction_fit,
            fraction_evaluate=self.config.fraction_fit,
            min_fit_clients=self.config.min_clients,
            min_evaluate_clients=self.config.min_clients,
            min_available_clients=self.config.min_clients,
            on_fit_config_fn=self._get_fit_config,
            on_evaluate_config_fn=self._get_evaluate_config,
            fit_metrics_aggregation_fn=fit_metrics_aggregation_fn,
            evaluate_metrics_aggregation_fn=evaluate_metrics_aggregation_fn,
        )
        
        return strategy
    
    def _get_fit_config(self, server_round: int) -> Dict:
        """Return fit configuration for clients."""
        config = {
            "local_epochs": self.config.local_epochs,
            "learning_rate": self.config.learning_rate,
        }
        
        # Add auth token if enabled
        if self.config.enable_auth and self.auth_token:
            config["auth_token"] = self.auth_token
        
        return config
    
    def _get_evaluate_config(self, server_round: int) -> Dict:
        """Return evaluate configuration for clients."""
        return {}
    
    def start_server(
        self,
        server_address: str = "0.0.0.0:8080",
        num_rounds: Optional[int] = None
    ):
        """
        Start Flower server.
        
        Args:
            server_address: Server address (host:port)
            num_rounds: Number of federated rounds (uses config if None)
        """
        if self.is_running:
            logger.warning("Server is already running")
            return
        
        num_rounds = num_rounds or self.config.num_rounds
        
        # Create strategy
        strategy = self.create_strategy()
        
        # Create server config
        server_config = ServerConfig(num_rounds=num_rounds)
        
        # Initialize server
        if self.client_fn:
            # Simulation mode: use client_fn
            self.server = Server(
                client_manager=None,
                strategy=strategy
            )
        else:
            # Real mode: wait for clients to connect
            from flwr.server import SimpleClientManager
            client_manager = SimpleClientManager()
            self.server = Server(
                client_manager=client_manager,
                strategy=strategy
            )
        
        # Start server in background thread
        self.is_running = True
        
        def run_server():
            try:
                import flwr.server.app as app
                app.start_server(
                    server_address=server_address,
                    config=server_config,
                    strategy=strategy,
                    client_manager=self.server.client_manager if hasattr(self.server, 'client_manager') else None,
                    force_final_distributed_eval=False
                )
            except Exception as e:
                logger.error(f"Server error: {e}")
                self.is_running = False
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        logger.info(f"Flower server started on {server_address}")
    
    def stop_server(self):
        """Stop Flower server."""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Flower server stopped")
    
    def run_federated_learning(
        self,
        server_address: str = "0.0.0.0:8080"
    ) -> Dict:
        """
        Run complete federated learning process.
        
        Args:
            server_address: Server address
        
        Returns:
            Dict with results
        """
        logger.info("Starting federated learning for recommender")
        start_time = datetime.now()
        
        # Start server
        self.start_server(server_address=server_address)
        
        # Wait for completion (in real deployment, this would be handled by Flower)
        if self.client_fn:
            # Simulation mode: run rounds manually
            from flwr.simulation import start_simulation
            
            strategy = self.create_strategy()
            
            # Run simulation
            hist = start_simulation(
                client_fn=self.client_fn,
                num_clients=self.config.num_simulated_clients,
                config=ServerConfig(num_rounds=self.config.num_rounds),
                strategy=strategy,
                client_resources={"num_cpus": 1, "num_gpus": 0},
            )
            
            # Extract metrics
            self.round_metrics = []
            for round_num, metrics in enumerate(hist.metrics_distributed_fit, 1):
                round_data = {
                    "round": round_num,
                    "metrics": metrics[1] if isinstance(metrics, tuple) else metrics,
                    "timestamp": datetime.now().isoformat()
                }
                self.round_metrics.append(round_data)
                self.current_round = round_num
                
                # Notify monitors
                self._notify_monitors(round_data)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        results = {
            "complete": True,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "rounds": self.round_metrics,
            "config": {
                "num_rounds": self.config.num_rounds,
                "num_clients": self.config.num_simulated_clients,
                "local_epochs": self.config.local_epochs,
                "learning_rate": self.config.learning_rate,
            }
        }
        
        # Save results
        self._save_results(results)
        
        logger.info(f"Federated learning complete: {duration:.2f}s")
        
        return results
    
    def _save_results(self, results: Dict):
        """Save results to file."""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {self.results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def add_monitoring_callback(self, callback: Callable[[Dict], None]):
        """Add callback for monitoring round progress."""
        self.monitoring_callbacks.append(callback)
    
    def _notify_monitors(self, metrics: Dict):
        """Notify all monitoring callbacks."""
        for callback in self.monitoring_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.warning(f"Error in monitoring callback: {e}")
    
    def get_status(self) -> Dict:
        """Get current server status."""
        return {
            "is_running": self.is_running,
            "current_round": self.current_round,
            "total_rounds": self.config.num_rounds,
            "round_metrics": self.round_metrics[-5:] if self.round_metrics else [],
            "progress_percent": (self.current_round / self.config.num_rounds * 100) if self.config.num_rounds > 0 else 0
        }
    
    def get_metrics_history(self) -> Dict:
        """Get complete metrics history for visualization."""
        if not self.round_metrics:
            return {
                "rounds": [],
                "loss_history": [],
                "accuracy_history": [],
                "precision_history": [],
                "client_counts": []
            }
        
        return {
            "rounds": [r.get("round", i+1) for i, r in enumerate(self.round_metrics)],
            "loss_history": [r.get("metrics", {}).get("loss", 1.0) for r in self.round_metrics],
            "accuracy_history": [r.get("metrics", {}).get("accuracy", 0.0) for r in self.round_metrics],
            "precision_history": [r.get("metrics", {}).get("precision", 0.0) for r in self.round_metrics],
            "client_counts": [r.get("metrics", {}).get("num_clients", 0) for r in self.round_metrics],
            "timestamps": [r.get("timestamp", "") for r in self.round_metrics]
        }

