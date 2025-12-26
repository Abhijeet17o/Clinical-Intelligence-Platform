"""
Federated Learning Data Loader

Loads audio files and transcripts from data/sessions/ for Whisper fine-tuning.
Supports IID and non-IID data splits for federated learning.
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import whisper
import librosa

logger = logging.getLogger(__name__)


class WhisperDataset(Dataset):
    """
    PyTorch Dataset for Whisper fine-tuning.
    Loads audio files and their corresponding transcripts.
    """
    
    def __init__(
        self,
        audio_files: List[str],
        transcripts: List[str],
        model_name: str = "base",
        device: str = "cpu"
    ):
        """
        Initialize Whisper dataset.
        
        Args:
            audio_files: List of paths to audio files
            transcripts: List of transcript texts
            model_name: Whisper model name (for tokenizer)
            device: Device to load model on
        """
        if len(audio_files) != len(transcripts):
            raise ValueError(f"Mismatch: {len(audio_files)} audio files, {len(transcripts)} transcripts")
        
        self.audio_files = audio_files
        self.transcripts = transcripts
        self.device = device
        
        # Load Whisper tokenizer
        self.model = whisper.load_model(model_name, device=device)
        self.tokenizer = whisper.tokenizer.get_tokenizer(
            multilingual=True,
            language=None,
            task="transcribe"
        )
        
        logger.info(f"Initialized WhisperDataset with {len(audio_files)} samples")
    
    def __len__(self):
        return len(self.audio_files)
    
    def __getitem__(self, idx):
        """
        Get a single sample.
        
        Returns:
            dict with 'audio' (mel spectrogram) and 'text' (tokenized transcript)
        """
        audio_path = self.audio_files[idx]
        transcript = self.transcripts[idx]
        
        # Load and preprocess audio
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.device)
        
        # Tokenize transcript
        tokens = self.tokenizer.encode(transcript)
        tokens = torch.tensor(tokens, dtype=torch.long, device=self.device)
        
        return {
            "mel": mel,
            "tokens": tokens,
            "text": transcript,
            "audio_path": audio_path
        }


class FLDataLoader:
    """
    Federated Learning Data Loader.
    
    Manages data loading and splitting for federated learning clients.
    """
    
    def __init__(
        self,
        data_dir: str = "data/sessions",
        whisper_model: str = "base",
        device: str = "cpu"
    ):
        """
        Initialize FL data loader.
        
        Args:
            data_dir: Root directory containing session data
            whisper_model: Whisper model name
            device: Device for processing
        """
        self.data_dir = Path(data_dir)
        self.whisper_model = whisper_model
        self.device = device
        self.audio_transcript_pairs: List[Tuple[str, str]] = []
        
        logger.info(f"Initializing FLDataLoader with data_dir={data_dir}")
        self._discover_data()
    
    def _discover_data(self):
        """Discover all audio files and transcripts in data directory."""
        self.audio_transcript_pairs = []
        
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist")
            return
        
        # Search for transcript JSON files
        for transcript_file in self.data_dir.rglob("*.json"):
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                transcript = data.get('transcript', '').strip()
                if not transcript:
                    continue
                
                # Find corresponding audio file
                # Check common locations: same directory, parent directory, or temp_audio
                session_dir = transcript_file.parent
                patient_id = data.get('patient_id', '')
                
                # Try to find audio file
                audio_file = None
                
                # Check same directory
                for ext in ['.wav', '.mp3', '.m4a', '.flac']:
                    audio_candidate = session_dir / f"recording{ext}"
                    if audio_candidate.exists():
                        audio_file = str(audio_candidate)
                        break
                
                # Check parent directory
                if not audio_file:
                    for ext in ['.wav', '.mp3', '.m4a', '.flac']:
                        audio_candidate = session_dir.parent / f"recording{ext}"
                        if audio_candidate.exists():
                            audio_file = str(audio_candidate)
                            break
                
                # Check temp_audio directory
                if not audio_file:
                    temp_audio_dir = self.data_dir.parent / "temp_audio"
                    if temp_audio_dir.exists():
                        for audio_file_path in temp_audio_dir.glob(f"*{patient_id}*"):
                            if audio_file_path.suffix in ['.wav', '.mp3', '.m4a', '.flac']:
                                audio_file = str(audio_file_path)
                                break
                
                if audio_file and os.path.exists(audio_file):
                    self.audio_transcript_pairs.append((audio_file, transcript))
                else:
                    logger.debug(f"No audio file found for transcript {transcript_file}")
            
            except Exception as e:
                logger.warning(f"Error processing {transcript_file}: {e}")
                continue
        
        logger.info(f"Discovered {len(self.audio_transcript_pairs)} audio-transcript pairs")
    
    def split_data(
        self,
        num_clients: int,
        split_type: str = "iid",
        seed: Optional[int] = None
    ) -> List[List[Tuple[str, str]]]:
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
        
        if len(self.audio_transcript_pairs) == 0:
            logger.warning("No data available for splitting")
            return [[] for _ in range(num_clients)]
        
        if split_type == "iid":
            # Random shuffle and split evenly
            indices = np.random.permutation(len(self.audio_transcript_pairs))
            splits = np.array_split(indices, num_clients)
            client_data = [
                [self.audio_transcript_pairs[idx] for idx in split]
                for split in splits
            ]
        
        elif split_type == "non-iid":
            # Non-IID: Sort by some feature (e.g., transcript length) and split
            # This creates heterogeneous data distribution
            sorted_pairs = sorted(
                self.audio_transcript_pairs,
                key=lambda x: len(x[1])  # Sort by transcript length
            )
            
            # Split into num_clients chunks with varying sizes
            chunk_sizes = []
            total = len(sorted_pairs)
            for i in range(num_clients):
                # Create varying chunk sizes (some clients get more data)
                base_size = total // num_clients
                variation = int(base_size * 0.3 * np.random.randn())
                size = max(1, base_size + variation)
                chunk_sizes.append(size)
            
            # Normalize to total
            total_allocated = sum(chunk_sizes)
            if total_allocated != total:
                chunk_sizes = [int(s * total / total_allocated) for s in chunk_sizes]
                # Adjust for rounding
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
            logger.info(f"Client {i}: {len(data)} samples")
        
        return client_data
    
    def get_client_dataset(
        self,
        client_data: List[Tuple[str, str]],
        batch_size: int = 1
    ) -> DataLoader:
        """
        Create a DataLoader for a specific client's data.
        
        Args:
            client_data: List of (audio_file, transcript) tuples for this client
            batch_size: Batch size for training
        
        Returns:
            PyTorch DataLoader
        """
        if len(client_data) == 0:
            logger.warning("No data for client, creating empty dataset")
            # Create empty dataset
            audio_files = []
            transcripts = []
        else:
            audio_files, transcripts = zip(*client_data)
            audio_files = list(audio_files)
            transcripts = list(transcripts)
        
        dataset = WhisperDataset(
            audio_files=audio_files,
            transcripts=transcripts,
            model_name=self.whisper_model,
            device=self.device
        )
        
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0,  # Set to 0 to avoid multiprocessing issues
            pin_memory=False
        )
    
    def get_total_samples(self) -> int:
        """Get total number of available samples."""
        return len(self.audio_transcript_pairs)
    
    def refresh_data(self):
        """Re-discover data (useful if new data is added)."""
        self._discover_data()

