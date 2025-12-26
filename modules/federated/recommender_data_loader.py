"""
Federated Learning Data Loader for Recommender System

Loads prescription data (symptoms -> medicines) from database and EHR records
for federated learning of the hybrid recommender model.
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommenderDataset:
    """
    Dataset for recommender federated learning.
    Contains symptoms -> medicines pairs from prescription history.
    """
    
    def __init__(
        self,
        data_pairs: List[Tuple[str, List[str]]]
    ):
        """
        Initialize recommender dataset.
        
        Args:
            data_pairs: List of (symptoms_text, [medicine_names]) tuples
        """
        self.data_pairs = data_pairs
        logger.info(f"Initialized RecommenderDataset with {len(data_pairs)} samples")
    
    def __len__(self):
        return len(self.data_pairs)
    
    def __getitem__(self, idx):
        """Get a single sample."""
        symptoms, medicines = self.data_pairs[idx]
        return {
            "symptoms": symptoms,
            "medicines": medicines
        }
    
    def get_all_symptoms(self) -> List[str]:
        """Get all symptom texts."""
        return [pair[0] for pair in self.data_pairs]
    
    def get_all_medicines(self) -> List[List[str]]:
        """Get all medicine lists."""
        return [pair[1] for pair in self.data_pairs]


class RecommenderFLDataLoader:
    """
    Federated Learning Data Loader for Recommender System.
    
    Loads prescription data from database and splits it for federated learning.
    """
    
    def __init__(
        self,
        db_connection=None,
        data_dir: str = "data/sessions"
    ):
        """
        Initialize recommender FL data loader.
        
        Args:
            db_connection: Database connection for loading prescription data
            data_dir: Directory containing session data (for transcript-based data)
        """
        self.db = db_connection
        self.data_dir = Path(data_dir)
        self.data_pairs: List[Tuple[str, List[str]]] = []
        
        logger.info(f"Initializing RecommenderFLDataLoader")
        self._discover_data()
    
    def _discover_data(self):
        """Discover prescription data from database and session files."""
        self.data_pairs = []
        
        # Method 1: Load from database (prescription history)
        if self.db:
            try:
                patients = self.db.get_all_patients()
                
                for patient in patients:
                    ehr_data = patient.get('ehr_data', '{}')
                    if isinstance(ehr_data, str):
                        try:
                            ehr_data = json.loads(ehr_data) if ehr_data else {}
                        except:
                            ehr_data = {}
                    
                    # Get symptoms
                    symptoms_list = ehr_data.get('symptoms', [])
                    if isinstance(symptoms_list, list):
                        symptoms_text = ' '.join(str(s) for s in symptoms_list)
                    else:
                        symptoms_text = str(symptoms_list) if symptoms_list else ''
                    
                    # Get prescriptions
                    prescriptions = ehr_data.get('prescriptions', [])
                    for prescription in prescriptions:
                        medicines = prescription.get('medicines', [])
                        if medicines:
                            medicine_names = [
                                med.get('name', '') if isinstance(med, dict) else str(med)
                                for med in medicines
                                if med
                            ]
                            medicine_names = [m for m in medicine_names if m]  # Filter empty
                            
                            if symptoms_text and medicine_names:
                                self.data_pairs.append((symptoms_text, medicine_names))
                
                logger.info(f"Loaded {len(self.data_pairs)} prescription pairs from database")
            except Exception as e:
                logger.warning(f"Error loading from database: {e}")
        
        # Method 2: Load from transcript files (symptoms from transcripts)
        if self.data_dir.exists():
            try:
                for transcript_file in self.data_dir.rglob("*.json"):
                    try:
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        transcript = data.get('transcript', '').strip()
                        if not transcript:
                            continue
                        
                        # Try to find corresponding prescription in EHR
                        patient_id = data.get('patient_id', '')
                        if self.db:
                            patient = self.db.get_patient(patient_id)
                            if patient:
                                ehr_data = patient.get('ehr_data', '{}')
                                if isinstance(ehr_data, str):
                                    try:
                                        ehr_data = json.loads(ehr_data) if ehr_data else {}
                                    except:
                                        ehr_data = {}
                                
                                prescriptions = ehr_data.get('prescriptions', [])
                                for prescription in prescriptions:
                                    medicines = prescription.get('medicines', [])
                                    if medicines:
                                        medicine_names = [
                                            med.get('name', '') if isinstance(med, dict) else str(med)
                                            for med in medicines
                                            if med
                                        ]
                                        medicine_names = [m for m in medicine_names if m]
                                        
                                        if transcript and medicine_names:
                                            self.data_pairs.append((transcript, medicine_names))
                    except Exception as e:
                        logger.debug(f"Error processing {transcript_file}: {e}")
                        continue
                
                logger.info(f"Total prescription pairs discovered: {len(self.data_pairs)}")
            except Exception as e:
                logger.warning(f"Error loading from session files: {e}")
        
        if len(self.data_pairs) == 0:
            logger.warning("No prescription data found. Federated learning will use synthetic data.")
    
    def split_data(
        self,
        num_clients: int,
        split_type: str = "iid",
        seed: Optional[int] = None
    ) -> List[List[Tuple[str, List[str]]]]:
        """
        Split data among clients.
        
        Args:
            num_clients: Number of clients
            split_type: "iid" (independent and identically distributed) or "non-iid"
            seed: Random seed for reproducibility
        
        Returns:
            List of data splits, one per client
        """
        if seed is not None:
            np.random.seed(seed)
        
        if len(self.data_pairs) == 0:
            logger.warning("No data available for splitting, creating synthetic data")
            # Create minimal synthetic data for demonstration
            self.data_pairs = [
                ("fever headache", ["Paracetamol", "Ibuprofen"]),
                ("cough cold", ["Cough Syrup", "Decongestant"]),
                ("stomach pain", ["Antacid", "Omeprazole"]),
            ] * max(1, num_clients)
        
        if split_type == "iid":
            # Random shuffle and split evenly
            indices = np.random.permutation(len(self.data_pairs))
            splits = np.array_split(indices, num_clients)
            client_data = [
                [self.data_pairs[idx] for idx in split]
                for split in splits
            ]
        
        elif split_type == "non-iid":
            # Non-IID: Sort by symptom length and split
            sorted_pairs = sorted(
                self.data_pairs,
                key=lambda x: len(x[0])  # Sort by symptom text length
            )
            
            # Split into num_clients chunks with varying sizes
            chunk_sizes = []
            total = len(sorted_pairs)
            for i in range(num_clients):
                base_size = total // num_clients
                variation = int(base_size * 0.3 * np.random.randn())
                size = max(1, base_size + variation)
                chunk_sizes.append(size)
            
            # Normalize to total
            total_allocated = sum(chunk_sizes)
            if total_allocated != total:
                chunk_sizes = [int(s * total / total_allocated) for s in chunk_sizes]
                diff = total - sum(chunk_sizes)
                chunk_sizes[0] += diff
            
            client_data = []
            start_idx = 0
            for size in chunk_sizes:
                end_idx = start_idx + size
                client_data.append(sorted_pairs[start_idx:end_idx])
                start_idx = end_idx
        
        else:
            raise ValueError(f"Unknown split_type: {split_type}")
        
        # Log distribution
        for i, data in enumerate(client_data):
            logger.info(f"Client {i}: {len(data)} prescription pairs")
        
        return client_data
    
    def get_client_dataset(
        self,
        client_data: List[Tuple[str, List[str]]]
    ) -> RecommenderDataset:
        """
        Create a dataset for a specific client's data.
        
        Args:
            client_data: List of (symptoms, medicines) tuples for this client
        
        Returns:
            RecommenderDataset instance
        """
        return RecommenderDataset(client_data)
    
    def get_total_samples(self) -> int:
        """Get total number of available samples."""
        return len(self.data_pairs)
    
    def refresh_data(self):
        """Re-discover data (useful if new data is added)."""
        self._discover_data()

