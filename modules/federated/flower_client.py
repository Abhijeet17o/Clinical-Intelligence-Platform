"""
Flower Client Implementation

Implements Flower NumPyClient for federated learning with Whisper model.
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from flwr.client import NumPyClient, Client
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

from .model_trainer import WhisperTrainer
from .data_loader import FLDataLoader
from .utils import retry, safe_execute, validate_client_token

logger = logging.getLogger(__name__)


class WhisperFlowerClient(NumPyClient):
    """
    Flower client for Whisper model federated learning.
    """
    
    def __init__(
        self,
        client_id: str,
        client_data: List[Tuple[str, str]],
        config: Dict,
        data_loader: Optional[FLDataLoader] = None,
        auth_token: Optional[str] = None
    ):
        """
        Initialize Flower client.
        
        Args:
            client_id: Unique client identifier
            client_data: List of (audio_file, transcript) tuples for this client
            config: Configuration dictionary with training parameters
            data_loader: Optional FLDataLoader instance
            auth_token: Optional authentication token
        """
        self.client_id = client_id
        self.client_data = client_data
        self.config = config
        self.auth_token = auth_token or config.get("auth_token")
        
        # Initialize data loader if not provided
        if data_loader is None:
            self.data_loader = FLDataLoader(
                data_dir=config.get("data_dir", "data/sessions"),
                whisper_model=config.get("whisper_model", "base"),
                device=config.get("device", "cpu")
            )
        else:
            self.data_loader = data_loader
        
        # Create dataset for this client
        self.train_loader = self.data_loader.get_client_dataset(
            client_data=client_data,
            batch_size=config.get("batch_size", 1)
        )
        
        # Initialize trainer
        self.trainer = WhisperTrainer(
            model_name=config.get("whisper_model", "base"),
            freeze_encoder=config.get("freeze_encoder", True),
            device=config.get("device", "cpu"),
            checkpoint_dir=config.get("checkpoint_dir")
        )
        
        logger.info(f"Initialized Flower client {client_id} with {len(client_data)} samples")
    
    def get_parameters(self, ins: GetParametersIns) -> GetParametersRes:
        """
        Return current model parameters.
        
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
            parameters: Parameters from server
        """
        ndarrays = parameters_to_ndarrays(parameters)
        self.trainer.set_model_parameters(ndarrays)
        logger.info(f"[{self.client_id}] Updated model parameters from server")
    
    @retry(max_attempts=3, delay=1.0, exceptions=(Exception,))
    def fit(self, ins: FitIns) -> FitRes:
        """
        Train model on local data.
        
        Args:
            ins: FitIns instruction with parameters and config
        
        Returns:
            FitRes with updated parameters and metrics
        """
        # Validate authentication if enabled
        if self.config.get("enable_auth", False):
            config_token = ins.config.get("auth_token")
            if not validate_client_token(self.auth_token or "", config_token):
                raise ValueError("Authentication failed")
        
        # Set parameters from server
        self.set_parameters(ins.parameters)
        
        # Get training config
        config = ins.config
        local_epochs = config.get("local_epochs", self.config.get("local_epochs", 1))
        learning_rate = config.get("learning_rate", self.config.get("learning_rate", 0.001))
        
        logger.info(
            f"[{self.client_id}] Starting local training: "
            f"{local_epochs} epochs, lr={learning_rate}"
        )
        
        # Train for specified epochs
        metrics_list = []
        for epoch in range(local_epochs):
            metrics = self.trainer.train_epoch(
                dataloader=self.train_loader,
                learning_rate=learning_rate
            )
            metrics_list.append(metrics)
            logger.info(
                f"[{self.client_id}] Epoch {epoch+1}/{local_epochs}: "
                f"loss={metrics['loss']:.4f}, wer={metrics['wer']:.4f}"
            )
        
        # Get final metrics (average over epochs)
        final_metrics = {
            "loss": np.mean([m["loss"] for m in metrics_list]),
            "wer": np.mean([m["wer"] for m in metrics_list]),
            "num_samples": len(self.client_data),
            "num_epochs": local_epochs
        }
        
        # Get updated parameters
        updated_parameters = self.trainer.get_model_parameters()
        parameters_proto = ndarrays_to_parameters(updated_parameters)
        
        logger.info(
            f"[{self.client_id}] Training complete: "
            f"loss={final_metrics['loss']:.4f}, wer={final_metrics['wer']:.4f}"
        )
        
        return FitRes(
            parameters=parameters_proto,
            num_examples=len(self.client_data),
            metrics=final_metrics
        )
    
    @retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
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
        
        # Evaluate
        metrics = self.trainer.evaluate(dataloader=self.train_loader)
        
        logger.info(
            f"[{self.client_id}] Evaluation complete: "
            f"loss={metrics['loss']:.4f}, wer={metrics['wer']:.4f}"
        )
        
        return EvaluateRes(
            loss=float(metrics["loss"]),
            num_examples=metrics.get("num_samples", len(self.client_data)),
            metrics=metrics
        )


def create_client_fn(
    client_data_splits: List[List[Tuple[str, str]]],
    config: Dict
) -> callable:
    """
    Create a function that returns a client instance.
    
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
        
        return WhisperFlowerClient(
            client_id=f"client_{cid}",
            client_data=client_data,
            config=config
        )
    
    return client_fn

