"""
EHR Pipeline - Main Entry Point
Run this script to process patient consultations through the complete pipeline
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from load_env import load_env
load_env()

from core.pipeline_manager import PipelineManager
from core.session_manager import SessionManager


def main():
    """Main entry point for the EHR pipeline"""
    
    print("\n" + "="*70)
    print("🏥 ELECTRONIC HEALTH RECORD (EHR) PIPELINE SYSTEM")
    print("="*70)
    print("\nThis system will:")
    print("  1. Record or import patient-doctor conversation audio")
    print("  2. Transcribe the audio using AI (Whisper)")
    print("  3. Auto-fill patient EHR profile with extracted information")
    print("\n" + "="*70)
    
    # Initialize pipeline
    pipeline = PipelineManager()
    
    # Get patient information
    print("\n📋 PATIENT INFORMATION")
    print("-"*70)
    
    patient_id = input("Enter Patient ID (e.g., PAT001): ").strip()
    if not patient_id:
        print("❌ Patient ID is required!")
        return
    
    patient_name = input("Enter Patient Name: ").strip()
    patient_age = input("Enter Patient Age: ").strip()
    doctor_id = input("Enter Doctor ID (e.g., DOC001): ").strip()
    
    if not doctor_id:
        print("❌ Doctor ID is required!")
        return
    
    # Get audio source
    print("\n🎤 AUDIO SOURCE")
    print("-"*70)
    print("Choose audio source:")
    print("  1. Use existing audio file")
    print("  2. Record new audio (30 seconds)")
    print("  3. Record new audio (custom duration)")
    
    choice = input("\nEnter choice (1/2/3) [default: 1]: ").strip()
    
    audio_file = None
    duration = 30
    
    if choice == '2':
        print("\n📌 Will record 30 seconds of audio")
    elif choice == '3':
        try:
            duration = int(input("Enter recording duration in seconds: ").strip())
            print(f"\n📌 Will record {duration} seconds of audio")
        except ValueError:
            print("❌ Invalid duration. Using 30 seconds.")
    else:
        # Use existing file
        audio_file = input("Enter path to audio file (or press Enter to browse): ").strip()
        
        if not audio_file:
            # List available audio files
            recordings_dir = "recordings"
            if os.path.exists(recordings_dir):
                audio_files = [f for f in os.listdir(recordings_dir) 
                              if f.endswith(('.wav', '.mp3', '.m4a', '.flac'))]
                
                if audio_files:
                    print(f"\nAvailable audio files in '{recordings_dir}':")
                    for i, f in enumerate(audio_files, 1):
                        print(f"  {i}. {f}")
                    
                    try:
                        file_choice = int(input(f"\nSelect file (1-{len(audio_files)}): ").strip())
                        if 1 <= file_choice <= len(audio_files):
                            audio_file = os.path.join(recordings_dir, audio_files[file_choice - 1])
                    except:
                        pass
        
        if not audio_file or not os.path.exists(audio_file):
            print("❌ Audio file not found. Will record new audio instead.")
            audio_file = None
    
    # Run pipeline
    print("\n" + "="*70)
    print("🚀 STARTING PIPELINE")
    print("="*70)
    
    result = pipeline.run_complete_pipeline(
        patient_id=patient_id,
        doctor_id=doctor_id,
        patient_name=patient_name,
        patient_age=patient_age,
        audio_file_path=audio_file,
        duration=duration
    )
    
    if result:
        session_id = result["session_id"]
        
        # Display results
        print("\n📄 VIEW RESULTS")
        print("-"*70)
        view_choice = input("\nWould you like to view the extracted EHR data? (y/n): ").strip().lower()
        
        if view_choice == 'y':
            import json
            ehr_file = pipeline.session_manager.get_session_file(session_id, "ehr")
            
            if ehr_file and os.path.exists(ehr_file):
                with open(ehr_file, 'r', encoding='utf-8') as f:
                    ehr_data = json.load(f)
                
                print("\n" + "="*70)
                print("📋 EXTRACTED EHR PROFILE")
                print("="*70)
                print(json.dumps(ehr_data, indent=2))
                print("="*70)
        
        print(f"\n✅ All session data saved in: data/sessions/{session_id}/")
        print(f"\nTo view this session later, use: python view_session.py {session_id}")
    else:
        print("\n❌ Pipeline execution failed. Check the logs above for details.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
