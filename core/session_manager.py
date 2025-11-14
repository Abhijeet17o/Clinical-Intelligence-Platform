"""
Session Manager - Manages patient consultation sessions with proper tracking
Each session has a unique session_id and tracks all patient data through the pipeline
"""

import json
import os
from datetime import datetime
import shutil


class SessionManager:
    """Manages patient consultation sessions"""
    
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self.sessions_dir = os.path.join(base_dir, "sessions")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directory structure"""
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "recordings"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "transcripts"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "ehr_profiles"), exist_ok=True)
    
    def create_session(self, patient_id, doctor_id, patient_name="", patient_age=""):
        """
        Create a new consultation session
        
        Args:
            patient_id (str): Unique patient identifier
            doctor_id (str): Doctor identifier
            patient_name (str): Patient name (optional)
            patient_age (str): Patient age (optional)
        
        Returns:
            dict: Session information with session_id
        """
        # Generate session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{patient_id}_{timestamp}"
        
        # Create session directory
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create session metadata
        session_data = {
            "session_id": session_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "pipeline_stages": {
                "recording": "pending",
                "transcription": "pending",
                "ehr_autofill": "pending"
            },
            "files": {
                "audio": None,
                "transcript": None,
                "ehr": None
            }
        }
        
        # Save session metadata
        metadata_path = os.path.join(session_dir, "session_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Session created: {session_id}")
        return session_data
    
    def get_session(self, session_id):
        """Load session data"""
        metadata_path = os.path.join(self.sessions_dir, session_id, "session_metadata.json")
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Session not found: {session_id}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_session(self, session_id, updates):
        """Update session metadata"""
        session_data = self.get_session(session_id)
        session_data.update(updates)
        session_data["updated_at"] = datetime.now().isoformat()
        
        metadata_path = os.path.join(self.sessions_dir, session_id, "session_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        
        return session_data
    
    def update_stage(self, session_id, stage, status):
        """Update pipeline stage status"""
        session_data = self.get_session(session_id)
        session_data["pipeline_stages"][stage] = status
        
        metadata_path = os.path.join(self.sessions_dir, session_id, "session_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
    
    def add_file(self, session_id, file_type, file_path):
        """Register a file with the session"""
        session_data = self.get_session(session_id)
        
        # Copy file to session directory
        session_dir = os.path.join(self.sessions_dir, session_id)
        filename = os.path.basename(file_path)
        dest_path = os.path.join(session_dir, filename)
        
        if file_path != dest_path:
            shutil.copy2(file_path, dest_path)
        
        # Update session metadata
        session_data["files"][file_type] = filename
        
        metadata_path = os.path.join(session_dir, "session_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        
        return dest_path
    
    def get_session_file(self, session_id, file_type):
        """Get path to a session file"""
        session_data = self.get_session(session_id)
        filename = session_data["files"].get(file_type)
        
        if not filename:
            return None
        
        return os.path.join(self.sessions_dir, session_id, filename)
    
    def list_sessions(self, patient_id=None):
        """List all sessions, optionally filtered by patient_id"""
        sessions = []
        
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        for session_id in os.listdir(self.sessions_dir):
            try:
                session_data = self.get_session(session_id)
                
                if patient_id is None or session_data["patient_id"] == patient_id:
                    sessions.append(session_data)
            except:
                continue
        
        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions
    
    def get_session_dir(self, session_id):
        """Get the directory path for a session"""
        return os.path.join(self.sessions_dir, session_id)
