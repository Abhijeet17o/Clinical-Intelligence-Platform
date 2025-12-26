"""
Client Manager for Federated Learning

Manages client registration, lifecycle, and health monitoring for both
local (multi-process) and distributed deployments.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ClientStatus(Enum):
    """Client status enumeration."""
    REGISTERED = "registered"
    TRAINING = "training"
    IDLE = "idle"
    FAILED = "failed"
    OFFLINE = "offline"


@dataclass
class ClientInfo:
    """Information about a federated learning client."""
    client_id: str
    status: ClientStatus = ClientStatus.REGISTERED
    data_size: int = 0
    last_heartbeat: Optional[datetime] = None
    registered_at: datetime = field(default_factory=datetime.now)
    capabilities: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    failure_count: int = 0
    retry_count: int = 0


class ClientManager:
    """
    Manages federated learning clients.
    
    Supports both local (multi-process) and distributed (network) clients.
    """
    
    def __init__(
        self,
        heartbeat_timeout: int = 60,
        max_failures: int = 3,
        deployment_mode: str = "hybrid"
    ):
        """
        Initialize client manager.
        
        Args:
            heartbeat_timeout: Seconds before considering client offline
            max_failures: Max failures before marking client as failed
            deployment_mode: "local", "distributed", or "hybrid"
        """
        self.heartbeat_timeout = heartbeat_timeout
        self.max_failures = max_failures
        self.deployment_mode = deployment_mode
        
        # Client registry
        self.clients: Dict[str, ClientInfo] = {}
        self.lock = threading.Lock()
        
        # Health monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        logger.info(f"Initialized ClientManager (mode={deployment_mode})")
    
    def register_client(
        self,
        client_id: str,
        data_size: int = 0,
        capabilities: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a new client.
        
        Args:
            client_id: Unique client identifier
            data_size: Number of data samples
            capabilities: Client capabilities (e.g., GPU support)
            metadata: Additional metadata
        
        Returns:
            True if registered successfully
        """
        with self.lock:
            if client_id in self.clients:
                logger.warning(f"Client {client_id} already registered, updating")
                # Update existing client
                client = self.clients[client_id]
                client.data_size = data_size
                client.capabilities.update(capabilities or {})
                client.metadata.update(metadata or {})
                client.status = ClientStatus.REGISTERED
                client.last_heartbeat = datetime.now()
                return True
            
            client = ClientInfo(
                client_id=client_id,
                data_size=data_size,
                capabilities=capabilities or {},
                metadata=metadata or {},
                last_heartbeat=datetime.now()
            )
            
            self.clients[client_id] = client
            logger.info(f"Registered client {client_id} (data_size={data_size})")
            
            # Start monitoring if not already started
            if not self.monitoring_active:
                self.start_monitoring()
            
            return True
    
    def unregister_client(self, client_id: str) -> bool:
        """
        Unregister a client.
        
        Args:
            client_id: Client identifier
        
        Returns:
            True if unregistered successfully
        """
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Unregistered client {client_id}")
                return True
            return False
    
    def update_client_status(
        self,
        client_id: str,
        status: ClientStatus
    ) -> bool:
        """
        Update client status.
        
        Args:
            client_id: Client identifier
            status: New status
        
        Returns:
            True if updated successfully
        """
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id].status = status
                self.clients[client_id].last_heartbeat = datetime.now()
                return True
            return False
    
    def record_heartbeat(self, client_id: str) -> bool:
        """
        Record client heartbeat.
        
        Args:
            client_id: Client identifier
        
        Returns:
            True if client exists
        """
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id].last_heartbeat = datetime.now()
                self.clients[client_id].failure_count = 0  # Reset on heartbeat
                return True
            return False
    
    def record_failure(self, client_id: str) -> bool:
        """
        Record client failure.
        
        Args:
            client_id: Client identifier
        
        Returns:
            True if client exists
        """
        with self.lock:
            if client_id in self.clients:
                client = self.clients[client_id]
                client.failure_count += 1
                
                if client.failure_count >= self.max_failures:
                    client.status = ClientStatus.FAILED
                    logger.warning(f"Client {client_id} marked as failed ({client.failure_count} failures)")
                
                return True
            return False
    
    def get_client(self, client_id: str) -> Optional[ClientInfo]:
        """Get client information."""
        with self.lock:
            return self.clients.get(client_id)
    
    def get_active_clients(self) -> List[ClientInfo]:
        """Get list of active (non-failed, non-offline) clients."""
        with self.lock:
            now = datetime.now()
            active = []
            
            for client in self.clients.values():
                # Check if offline
                if client.last_heartbeat:
                    time_since_heartbeat = (now - client.last_heartbeat).total_seconds()
                    if time_since_heartbeat > self.heartbeat_timeout:
                        client.status = ClientStatus.OFFLINE
                
                if client.status not in [ClientStatus.FAILED, ClientStatus.OFFLINE]:
                    active.append(client)
            
            return active
    
    def get_client_count(self) -> int:
        """Get total number of registered clients."""
        with self.lock:
            return len(self.clients)
    
    def get_active_client_count(self) -> int:
        """Get number of active clients."""
        return len(self.get_active_clients())
    
    def start_monitoring(self):
        """Start health monitoring thread."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor():
            while self.monitoring_active:
                try:
                    self._check_client_health()
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    logger.error(f"Error in health monitoring: {e}")
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started client health monitoring")
    
    def stop_monitoring(self):
        """Stop health monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped client health monitoring")
    
    def _check_client_health(self):
        """Check health of all clients."""
        with self.lock:
            now = datetime.now()
            
            for client_id, client in self.clients.items():
                if client.last_heartbeat:
                    time_since_heartbeat = (now - client.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        if client.status != ClientStatus.OFFLINE:
                            logger.warning(
                                f"Client {client_id} appears offline "
                                f"(last heartbeat: {time_since_heartbeat:.1f}s ago)"
                            )
                            client.status = ClientStatus.OFFLINE
    
    def get_summary(self) -> Dict:
        """Get summary of client status."""
        with self.lock:
            status_counts = {}
            for status in ClientStatus:
                status_counts[status.value] = sum(
                    1 for c in self.clients.values() if c.status == status
                )
            
            return {
                "total_clients": len(self.clients),
                "active_clients": self.get_active_client_count(),
                "status_counts": status_counts,
                "deployment_mode": self.deployment_mode
            }
    
    def get_client_details(self) -> List[Dict]:
        """Get detailed information about all clients."""
        with self.lock:
            return [
                {
                    "client_id": client.client_id,
                    "status": client.status.value,
                    "data_size": client.data_size,
                    "last_heartbeat": client.last_heartbeat.isoformat() if client.last_heartbeat else None,
                    "registered_at": client.registered_at.isoformat(),
                    "failure_count": client.failure_count,
                    "capabilities": client.capabilities,
                    "metadata": client.metadata
                }
                for client in self.clients.values()
            ]

