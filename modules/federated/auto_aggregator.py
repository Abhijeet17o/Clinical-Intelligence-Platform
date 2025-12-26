"""
Automatic Federated Aggregation Service

Background process that periodically aggregates weight updates
from incremental learning across multiple clients/hospitals.
"""

import logging
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class AutoAggregator:
    """
    Automatically aggregates weight updates from incremental learning.
    
    Runs in the background and periodically:
    1. Collects weight updates from local learning
    2. Aggregates across multiple "hospitals" (simulated clients)
    3. Distributes aggregated weights back
    """
    
    def __init__(
        self,
        aggregation_interval: int = 300,  # 5 minutes
        min_updates_before_aggregate: int = 5,
        enabled: bool = True
    ):
        """
        Initialize auto aggregator.
        
        Args:
            aggregation_interval: Seconds between aggregation cycles
            min_updates_before_aggregate: Minimum local updates before aggregating
            enabled: Whether aggregation is enabled
        """
        self.aggregation_interval = aggregation_interval
        self.min_updates_before_aggregate = min_updates_before_aggregate
        self.enabled = enabled
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._local_updates: List[Dict] = []
        self._last_aggregation = None
        self._aggregation_count = 0
        
        logger.info(f"AutoAggregator initialized (interval: {aggregation_interval}s, enabled: {enabled})")
    
    def start(self):
        """Start the background aggregation thread."""
        if not self.enabled:
            logger.info("AutoAggregator is disabled")
            return
        
        if self._running:
            logger.warning("AutoAggregator is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._aggregation_loop, daemon=True)
        self._thread.start()
        logger.info("AutoAggregator started")
    
    def stop(self):
        """Stop the background aggregation thread."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("AutoAggregator stopped")
    
    def add_local_update(self, weights: Dict[str, float], metadata: Optional[Dict] = None):
        """
        Add a local weight update to the aggregation queue.
        
        Args:
            weights: Dictionary of model weights
            metadata: Optional metadata about the update
        """
        update = {
            'weights': weights.copy(),
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self._local_updates.append(update)
        logger.debug(f"Added local update (total: {len(self._local_updates)})")
    
    def _aggregation_loop(self):
        """Main aggregation loop running in background thread."""
        while self._running:
            try:
                time.sleep(self.aggregation_interval)
                
                if not self._running:
                    break
                
                # Check if we have enough updates
                if len(self._local_updates) >= self.min_updates_before_aggregate:
                    self._perform_aggregation()
                else:
                    logger.debug(
                        f"Not enough updates for aggregation "
                        f"({len(self._local_updates)}/{self.min_updates_before_aggregate})"
                    )
            
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}", exc_info=True)
    
    def _perform_aggregation(self):
        """Perform federated aggregation of weight updates."""
        if not self._local_updates:
            return
        
        try:
            logger.info(f"Performing federated aggregation with {len(self._local_updates)} updates")
            
            # Aggregate weights using FedAvg
            aggregated_weights = self._fedavg_aggregate(self._local_updates)
            
            # Clear local updates after aggregation
            self._local_updates.clear()
            
            # Update last aggregation time
            self._last_aggregation = datetime.now()
            self._aggregation_count += 1
            
            logger.info(
                f"✅ Aggregation #{self._aggregation_count} complete. "
                f"New weights: {aggregated_weights}"
            )
            
            # In a real federated setup, you would:
            # 1. Send aggregated weights to FL server
            # 2. Server distributes to all clients
            # 3. Clients update their local models
            
            # For now, we just log it
            # In production, you'd integrate with RecommenderFLServerManager
            
        except Exception as e:
            logger.error(f"Error performing aggregation: {e}", exc_info=True)
    
    def _fedavg_aggregate(self, updates: List[Dict]) -> Dict[str, float]:
        """
        Federated Averaging (FedAvg) aggregation.
        
        Args:
            updates: List of weight update dictionaries
        
        Returns:
            Aggregated weights dictionary
        """
        if not updates:
            return {}
        
        # Get all model names
        all_models = set()
        for update in updates:
            all_models.update(update['weights'].keys())
        
        # Aggregate each model's weight
        aggregated = {}
        for model_name in all_models:
            # Average all weights for this model
            weights = [
                update['weights'].get(model_name, 0.0)
                for update in updates
            ]
            aggregated[model_name] = sum(weights) / len(weights)
        
        # Normalize to sum to 1
        total = sum(aggregated.values())
        if total > 0:
            aggregated = {k: v / total for k, v in aggregated.items()}
        
        return aggregated
    
    def get_status(self) -> Dict:
        """Get aggregator status."""
        return {
            'running': self._running,
            'enabled': self.enabled,
            'pending_updates': len(self._local_updates),
            'last_aggregation': self._last_aggregation.isoformat() if self._last_aggregation else None,
            'aggregation_count': self._aggregation_count,
            'next_aggregation_in': self.aggregation_interval if self._running else None
        }
    
    def trigger_aggregation_now(self):
        """Manually trigger aggregation (for testing)."""
        if len(self._local_updates) > 0:
            self._perform_aggregation()
        else:
            logger.warning("No updates to aggregate")

