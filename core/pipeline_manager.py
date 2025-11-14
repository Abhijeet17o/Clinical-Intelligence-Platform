"""
Pipeline Manager - Orchestrates the complete EHR pipeline
Manages the flow: Recording -> Transcription -> EHR Auto-fill
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import SessionManager
from modules import audio_recorder, transcription_engine, ehr_autofill

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineManager:
    """Manages the complete EHR processing pipeline"""
    
    def __init__(self):
        self.session_manager = SessionManager()
    
    def start_new_session(self, patient_id, doctor_id, patient_name="", patient_age=""):
        """
        Start a new patient consultation session
        
        Returns:
            str: session_id
        """
        session_data = self.session_manager.create_session(
            patient_id, doctor_id, patient_name, patient_age
        )
        return session_data["session_id"]
    
    def record_audio(self, session_id, audio_file_path=None, duration=30):
        """
        Step 1: Record or import audio for a session
        
        Args:
            session_id (str): Session identifier
            audio_file_path (str): Path to existing audio file, or None to record new
            duration (int): Recording duration if recording new audio
        
        Returns:
            str: Path to audio file
        """
        logger.info(f"[Session {session_id}] Step 1: Recording audio")
        
        try:
            self.session_manager.update_stage(session_id, "recording", "in_progress")
            
            if audio_file_path and os.path.exists(audio_file_path):
                # Use existing audio file
                logger.info(f"Using existing audio file: {audio_file_path}")
                final_path = audio_file_path
            else:
                # Record new audio
                logger.info(f"Recording new audio for {duration} seconds...")
                session_dir = self.session_manager.get_session_dir(session_id)
                output_dir = session_dir
                
                final_path = audio_recorder.record_audio(
                    duration=duration,
                    sample_rate=16000,
                    channels=1,
                    output_dir=output_dir
                )
                
                if not final_path:
                    raise Exception("Audio recording failed")
            
            # Register audio file with session
            self.session_manager.add_file(session_id, "audio", final_path)
            self.session_manager.update_stage(session_id, "recording", "completed")
            
            logger.info(f"✅ Audio recorded: {final_path}")
            return final_path
            
        except Exception as e:
            self.session_manager.update_stage(session_id, "recording", "failed")
            logger.error(f"❌ Recording failed: {e}")
            raise
    
    def transcribe_audio(self, session_id):
        """
        Step 2: Transcribe the audio using Whisper
        
        Args:
            session_id (str): Session identifier
        
        Returns:
            str: Path to transcript JSON file
        """
        logger.info(f"[Session {session_id}] Step 2: Transcribing audio")
        
        try:
            self.session_manager.update_stage(session_id, "transcription", "in_progress")
            
            # Get session data
            session_data = self.session_manager.get_session(session_id)
            audio_file = self.session_manager.get_session_file(session_id, "audio")
            
            if not audio_file:
                raise Exception("No audio file found for this session")
            
            # Get session directory for output
            session_dir = self.session_manager.get_session_dir(session_id)
            
            # Transcribe
            transcript_path = transcription_engine.transcribe_conversation(
                audio_file_path=audio_file,
                patient_id=session_data["patient_id"],
                doctor_id=session_data["doctor_id"],
                output_dir=session_dir
            )
            
            if not transcript_path:
                raise Exception("Transcription failed")
            
            # Register transcript with session
            self.session_manager.add_file(session_id, "transcript", transcript_path)
            self.session_manager.update_stage(session_id, "transcription", "completed")
            
            logger.info(f"✅ Transcription completed: {transcript_path}")
            return transcript_path
            
        except Exception as e:
            self.session_manager.update_stage(session_id, "transcription", "failed")
            logger.error(f"❌ Transcription failed: {e}")
            raise
    
    def autofill_ehr(self, session_id):
        """
        Step 3: Auto-fill EHR profile from transcript
        
        Args:
            session_id (str): Session identifier
        
        Returns:
            dict: Updated EHR data
        """
        logger.info(f"[Session {session_id}] Step 3: Auto-filling EHR")
        
        try:
            self.session_manager.update_stage(session_id, "ehr_autofill", "in_progress")
            
            # Get session data
            session_data = self.session_manager.get_session(session_id)
            transcript_file = self.session_manager.get_session_file(session_id, "transcript")
            
            if not transcript_file:
                raise Exception("No transcript file found for this session")
            
            # Create EHR template
            ehr_template = {
                'patient_id': session_data["patient_id"],
                'patient_name': session_data.get("patient_name", ""),
                'age': session_data.get("patient_age", ""),
                'symptoms': '',
                'allergies_mentioned': '',
                'lifestyle_notes': ''
            }
            
            # Auto-fill EHR
            updated_ehr = ehr_autofill.autofill_ehr(transcript_file, ehr_template)
            
            if not updated_ehr:
                raise Exception("EHR auto-fill failed")
            
            # Save EHR to session directory
            session_dir = self.session_manager.get_session_dir(session_id)
            ehr_path = os.path.join(session_dir, f"ehr_{session_data['patient_id']}.json")
            
            import json
            with open(ehr_path, 'w', encoding='utf-8') as f:
                json.dump(updated_ehr, f, indent=4, ensure_ascii=False)
            
            # Register EHR with session
            self.session_manager.add_file(session_id, "ehr", ehr_path)
            self.session_manager.update_stage(session_id, "ehr_autofill", "completed")
            self.session_manager.update_session(session_id, {"status": "completed"})
            
            logger.info(f"✅ EHR auto-filled: {ehr_path}")
            return updated_ehr
            
        except Exception as e:
            self.session_manager.update_stage(session_id, "ehr_autofill", "failed")
            logger.error(f"❌ EHR auto-fill failed: {e}")
            raise
    
    def run_complete_pipeline(self, patient_id, doctor_id, patient_name="", patient_age="", 
                             audio_file_path=None, duration=30):
        """
        Run the complete pipeline: Create Session -> Record -> Transcribe -> Auto-fill EHR
        
        Args:
            patient_id (str): Patient identifier
            doctor_id (str): Doctor identifier
            patient_name (str): Patient name
            patient_age (str): Patient age
            audio_file_path (str): Path to existing audio file (or None to record)
            duration (int): Recording duration if recording new
        
        Returns:
            dict: Complete session data
        """
        print("\n" + "="*70)
        print("🏥 STARTING COMPLETE EHR PIPELINE")
        print("="*70)
        
        # Create session
        session_id = self.start_new_session(patient_id, doctor_id, patient_name, patient_age)
        print(f"\n📋 Session ID: {session_id}")
        print(f"   Patient: {patient_name} ({patient_id})")
        print(f"   Doctor: {doctor_id}")
        
        try:
            # Step 1: Record audio
            print("\n🎤 Step 1/3: Recording Audio...")
            audio_path = self.record_audio(session_id, audio_file_path, duration)
            print(f"   ✅ Audio: {os.path.basename(audio_path)}")
            
            # Step 2: Transcribe
            print("\n📝 Step 2/3: Transcribing Audio (this may take a moment)...")
            transcript_path = self.transcribe_audio(session_id)
            print(f"   ✅ Transcript: {os.path.basename(transcript_path)}")
            
            # Step 3: Auto-fill EHR
            print("\n🏥 Step 3/3: Auto-filling EHR Profile...")
            ehr_data = self.autofill_ehr(session_id)
            print(f"   ✅ EHR Profile Updated")
            
            # Get final session data
            session_data = self.session_manager.get_session(session_id)
            
            print("\n" + "="*70)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"\n📁 Session Directory: data/sessions/{session_id}/")
            print(f"\nExtracted Information:")
            print(f"   • Symptoms: {len(ehr_data.get('symptoms', '').split(';'))} items")
            print(f"   • Allergies: {len(ehr_data.get('allergies_mentioned', '').split(';'))} items")
            print(f"   • Lifestyle: {len(ehr_data.get('lifestyle_notes', '').split(';'))} items")
            print("="*70)
            
            return session_data
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            logger.error(f"Pipeline error: {e}", exc_info=True)
            return None
