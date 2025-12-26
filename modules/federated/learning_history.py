"""
Learning History Management

Persistent storage and retrieval of federated learning events.
Saves learning history to JSON files so it persists across server restarts.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class LearningHistory:
    """
    Manages persistent storage of learning events.
    """
    
    def __init__(
        self,
        history_file: str = "data/fl_learning_history.json",
        stats_file: str = "data/fl_learning_stats.json"
    ):
        """
        Initialize learning history manager.
        
        Args:
            history_file: Path to learning history JSON file
            stats_file: Path to learning statistics JSON file
        """
        self.history_file = Path(history_file)
        self.stats_file = Path(stats_file)
        
        # Ensure directories exist
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        self.history: List[Dict] = self._load_history()
        self.stats: Dict = self._load_stats()
        
        logger.info(f"Loaded {len(self.history)} learning events from history")
    
    def _load_history(self) -> List[Dict]:
        """Load learning history from file."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('events', [])
        except Exception as e:
            logger.warning(f"Error loading history: {e}")
            return []
    
    def _load_stats(self) -> Dict:
        """Load learning statistics from file."""
        if not self.stats_file.exists():
            return {
                'total_learnings': 0,
                'today_count': 0,
                'last_learning': None,
                'weight_evolution': {},
                'medicine_patterns': {}
            }
        
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading stats: {e}")
            return {
                'total_learnings': 0,
                'today_count': 0,
                'last_learning': None,
                'weight_evolution': {},
                'medicine_patterns': {}
            }
    
    def _save_history(self):
        """Save learning history to file."""
        try:
            data = {
                'events': self.history,
                'last_updated': datetime.now().isoformat(),
                'total_events': len(self.history)
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def _save_stats(self):
        """Save learning statistics to file."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def add_learning_event(
        self,
        symptoms: str,
        recommended_medicines: List[str],
        selected_medicine: str,
        learning_result: Dict
    ):
        """
        Add a new learning event to history.
        
        Args:
            symptoms: Patient symptoms
            recommended_medicines: List of recommended medicine names
            selected_medicine: Medicine that was actually selected
            learning_result: Result from incremental learner
        """
        event = {
            'id': len(self.history) + 1,
            'timestamp': datetime.now().isoformat(),
            'symptoms': symptoms[:200] if len(symptoms) > 200 else symptoms,  # Truncate
            'recommended_medicines': recommended_medicines[:10],  # Top 10
            'selected_medicine': selected_medicine,
            'weights_before': learning_result.get('weights_before', {}),
            'weights_after': learning_result.get('weights_after', {}),
            'weight_changes': learning_result.get('weight_changes', {}),
            'learning_count': learning_result.get('learning_count', 0)
        }
        
        self.history.append(event)
        
        # Update stats
        self._update_stats(event)
        
        # Save to file
        self._save_history()
        self._save_stats()
        
        logger.info(f"Added learning event #{event['id']} to history")
    
    def _update_stats(self, event: Dict):
        """Update statistics from a new learning event."""
        # Total count
        self.stats['total_learnings'] = len(self.history)
        
        # Today's count
        today = datetime.now().date()
        today_count = sum(
            1 for event in self.history
            if datetime.fromisoformat(event['timestamp']).date() == today
        )
        self.stats['today_count'] = today_count
        
        # Last learning
        if self.history:
            self.stats['last_learning'] = self.history[-1]['timestamp']
        
        # Weight evolution (track weights over time)
        if 'weights_after' in event:
            timestamp = event['timestamp']
            if 'weight_evolution' not in self.stats:
                self.stats['weight_evolution'] = {}
            
            # Store weights at this timestamp
            self.stats['weight_evolution'][timestamp] = event['weights_after']
        
        # Medicine patterns (track symptom -> medicine mappings)
        if 'medicine_patterns' not in self.stats:
            self.stats['medicine_patterns'] = {}
        
        symptom_key = event['symptoms'][:50].lower()  # Use first 50 chars as key
        if symptom_key not in self.stats['medicine_patterns']:
            self.stats['medicine_patterns'][symptom_key] = {
                'symptoms': event['symptoms'],
                'medicines': [],
                'count': 0
            }
        
        if event['selected_medicine'] not in self.stats['medicine_patterns'][symptom_key]['medicines']:
            self.stats['medicine_patterns'][symptom_key]['medicines'].append(event['selected_medicine'])
        
        self.stats['medicine_patterns'][symptom_key]['count'] += 1
    
    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """Get most recent learning events."""
        return self.history[-limit:] if len(self.history) > limit else self.history
    
    def get_today_events(self) -> List[Dict]:
        """Get all learning events from today."""
        today = datetime.now().date()
        return [
            event for event in self.history
            if datetime.fromisoformat(event['timestamp']).date() == today
        ]
    
    def get_stats(self) -> Dict:
        """Get current learning statistics."""
        return self.stats.copy()
    
    def get_weight_evolution(self) -> List[Dict]:
        """Get weight evolution over time."""
        evolution = []
        for timestamp, weights in self.stats.get('weight_evolution', {}).items():
            evolution.append({
                'timestamp': timestamp,
                'weights': weights
            })
        
        # Sort by timestamp
        evolution.sort(key=lambda x: x['timestamp'])
        return evolution
    
    def get_learning_rate(self) -> float:
        """Calculate learning rate (events per hour)."""
        if len(self.history) < 2:
            return 0.0
        
        # Get time span
        first_time = datetime.fromisoformat(self.history[0]['timestamp'])
        last_time = datetime.fromisoformat(self.history[-1]['timestamp'])
        time_span = (last_time - first_time).total_seconds() / 3600  # hours
        
        if time_span == 0:
            return 0.0
        
        return len(self.history) / time_span

