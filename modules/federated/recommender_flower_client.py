"""
Flower Client Implementation for Recommender System

Implements Flower NumPyClient for federated learning with Hybrid Recommender.
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from flwr.client import NumPyClient
from flwr.common import (
    FitIns,
    FitRes,
    EvaluateIns,
    EvaluateRes,
    Parameters,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
    GetParametersIns,
    GetParametersRes,
)

from .recommender_trainer import RecommenderFLTrainer
from .recommender_data_loader import RecommenderFLDataLoader

logger = logging.getLogger(__name__)


class RecommenderFlowerClient(NumPyClient):
    """
    Flower client for Hybrid Recommender federated learning.
    """
    
    def __init__(
        self,
        client_id: str,
        client_data: List[Tuple[str, List[str]]],
        config: Dict,
        data_loader: Optional[RecommenderFLDataLoader] = None
    ):
        """
        Initialize Flower client for recommender.
        
        Args:
            client_id: Unique client identifier
            client_data: List of (symptoms, medicines) tuples for this client
            config: Configuration dictionary with training parameters
            data_loader: Optional RecommenderFLDataLoader instance
        """
        self.client_id = client_id
        self.client_data = client_data
        self.config = config
        
        # Initialize data loader if not provided
        if data_loader is None:
            self.data_loader = RecommenderFLDataLoader(
                db_connection=config.get("db_connection"),
                data_dir=config.get("data_dir", "data/sessions")
            )
        else:
            self.data_loader = data_loader
        
        # Create dataset for this client
        self.train_dataset = self.data_loader.get_client_dataset(client_data=client_data)
        
        # Initialize trainer
        self.trainer = RecommenderFLTrainer(
            db_connection=config.get("db_connection"),
            checkpoint_dir=config.get("checkpoint_dir")
        )
        
        logger.info(f"Initialized RecommenderFlowerClient {client_id} with {len(client_data)} samples")
    
    def get_parameters(self, ins: GetParametersIns) -> GetParametersRes:
        """
        Return current model parameters (ensemble weights).
        
        Args:
            ins: GetParametersIns instruction
        
        Returns:
            GetParametersRes with model parameters
        """
        parameters = self.trainer.get_model_parameters()
        parameters_proto = ndarrays_to_parameters(parameters)
        
        return GetParametersRes(parameters=parameters_proto)
    
    def set_parameters(self, parameters: Parameters) -> None:
        """
        Set model parameters from server.
        
        Args:
            parameters: Parameters from server (ensemble weights)
        """
        ndarrays = parameters_to_ndarrays(parameters)
        self.trainer.set_model_parameters(ndarrays)
        logger.info(f"[{self.client_id}] Updated ensemble weights from server")
    
    def fit(self, ins: FitIns) -> FitRes:
        """
        Train model on local prescription data.
        
        Args:
            ins: FitIns instruction with parameters and config
        
        Returns:
            FitRes with updated parameters and metrics
        """
        # Set parameters from server
        self.set_parameters(ins.parameters)
        
        # Get training config
        config = ins.config
        local_epochs = config.get("local_epochs", self.config.get("local_epochs", 1))
        learning_rate = config.get("learning_rate", self.config.get("learning_rate", 0.1))
        
        logger.info(
            f"[{self.client_id}] Starting local training: "
            f"{local_epochs} epochs, lr={learning_rate}"
        )
        
        # Get all medicines for training
        all_medicines = None
        if self.config.get("db_connection"):
            all_medicines = self.config["db_connection"].get_all_medicines()
        
        # Train for specified epochs
        metrics_list = []
        for epoch in range(local_epochs):
            metrics = self.trainer.train_epoch(
                dataset=self.train_dataset,
                learning_rate=learning_rate,
                all_medicines=all_medicines
            )
            metrics_list.append(metrics)
            logger.info(
                f"[{self.client_id}] Epoch {epoch+1}/{local_epochs}: "
                f"loss={metrics['loss']:.4f}, accuracy={metrics['accuracy']:.4f}"
            )
        
        # Get final metrics (average over epochs)
        final_metrics = {
            "loss": np.mean([m["loss"] for m in metrics_list]),
            "accuracy": np.mean([m["accuracy"] for m in metrics_list]),
            "precision": np.mean([m.get("precision", m["accuracy"]) for m in metrics_list]),
            "num_samples": len(self.client_data),
            "num_epochs": local_epochs
        }
        
        # Get updated parameters
        updated_parameters = self.trainer.get_model_parameters()
        parameters_proto = ndarrays_to_parameters(updated_parameters)
        
        logger.info(
            f"[{self.client_id}] Training complete: "
            f"loss={final_metrics['loss']:.4f}, accuracy={final_metrics['accuracy']:.4f}"
        )
        
        return FitRes(
            parameters=parameters_proto,
            num_examples=len(self.client_data),
            metrics=final_metrics
        )
    
    def evaluate(self, ins: EvaluateIns) -> EvaluateRes:
        """
        Evaluate model on local data.
        
        Args:
            ins: EvaluateIns instruction with parameters and config
        
        Returns:
            EvaluateRes with evaluation metrics
        """
        # Set parameters from server
        self.set_parameters(ins.parameters)
        
        logger.info(f"[{self.client_id}] Evaluating model")
        
        # Get all medicines for evaluation
        all_medicines = None
        if self.config.get("db_connection"):
            all_medicines = self.config["db_connection"].get_all_medicines()
        
        # Evaluate
        metrics = self.trainer.evaluate(
            dataset=self.train_dataset,
            all_medicines=all_medicines
        )
        
        logger.info(
            f"[{self.client_id}] Evaluation complete: "
            f"loss={metrics['loss']:.4f}, accuracy={metrics['accuracy']:.4f}"
        )
        
        return EvaluateRes(
            loss=float(metrics["loss"]),
            num_examples=metrics.get("num_samples", len(self.client_data)),
            metrics=metrics
        )


def create_recommender_client_fn(
    client_data_splits: List[List[Tuple[str, List[str]]]],
    config: Dict
) -> callable:
    """
    Create a function that returns a recommender client instance.
    
    This is used by Flower to create clients dynamically.
    
    Args:
        client_data_splits: List of data splits, one per client
        config: Configuration dictionary
    
    Returns:
        Function that takes cid (client ID) and returns NumPyClient
    """
    def client_fn(cid: str) -> NumPyClient:
        """Create a client for the given client ID."""
        client_idx = int(cid)
        if client_idx >= len(client_data_splits):
            raise ValueError(f"Client ID {cid} out of range")
        
        client_data = client_data_splits[client_idx]
        
        return RecommenderFlowerClient(
            client_id=f"client_{cid}",
            client_data=client_data,
            config=config
        )
    
    return client_fn

