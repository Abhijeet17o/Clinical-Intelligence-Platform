"""
Module 1: Transcription Engine
This module transcribes doctor-patient conversations using OpenAI's Whisper model
and saves the transcript to a structured JSON file.
"""

import whisper
import json
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def transcribe_conversation(audio_file_path, patient_id, doctor_id, output_dir=None):
    """
    Transcribes an audio conversation and saves it to a structured JSON file.
    
    Args:
        audio_file_path (str): Path to the audio file to transcribe
        patient_id (str): Unique identifier for the patient
        doctor_id (str): Unique identifier for the doctor
        output_dir (str, optional): Directory to save the JSON file. 
                                     Defaults to current working directory if not provided.
    
    Returns:
        str: File path of the created JSON file containing the transcript,
             or None if transcription fails
    
    Raises:
        ValueError: If input validation fails
        FileNotFoundError: If the audio file doesn't exist
        Exception: If transcription fails
    """
    
    try:
        # Input Validation
        if not audio_file_path or not isinstance(audio_file_path, str):
            error_msg = "audio_file_path must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(patient_id, str) or not patient_id:
            error_msg = "patient_id must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(doctor_id, str) or not doctor_id:
            error_msg = "doctor_id must be a non-empty string"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Verify audio file exists
        if not os.path.exists(audio_file_path):
            error_msg = f"Audio file not found: {audio_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Starting transcription for patient: {patient_id}")
        logger.info(f"Loading Whisper model...")
        
        # Load Whisper model (using 'base' model for balance of speed and accuracy)
        model = whisper.load_model("base")
        
        logger.info(f"Transcribing audio file: {audio_file_path}")
        # Transcribe the audio file
        result = model.transcribe(audio_file_path)
        
        # Get current timestamp in ISO 8601 format
        conversation_timestamp = datetime.now().isoformat()
        
        # Create the structured dictionary
        transcript_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "conversation_timestamp": conversation_timestamp,
            "transcript": result["text"]
        }
        
        # Create filename with patient_id and timestamp (safe for filesystems)
        # Convert ISO timestamp to filesystem-safe format
        timestamp_safe = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        json_filename = f"{patient_id}_{timestamp_safe}.json"
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()  # Default to current working directory
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Full path for the JSON file
        json_filepath = os.path.join(output_dir, json_filename)
        
        # Save to JSON file
        with open(json_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(transcript_data, json_file, indent=4, ensure_ascii=False)
        
        logger.info(f"Transcript saved successfully to: {json_filepath}")
        
        return json_filepath
    
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        return None
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}", exc_info=True)
        return None


if __name__ == '__main__':
    # Example usage
    print("="*60)
    print("Module 1: Transcription Engine - Example Usage")
    print("="*60)
    
    # Dummy parameters for demonstration
    audio_file = "sample_conversation.mp3"  # Replace with actual audio file path
    patient_id = "PAT123"
    doctor_id = "DOC456"
    output_directory = "transcripts"  # Optional: specify output directory
    
    print(f"\nAttempting to transcribe:")
    print(f"  Audio File: {audio_file}")
    print(f"  Patient ID: {patient_id}")
    print(f"  Doctor ID: {doctor_id}")
    print(f"  Output Dir: {output_directory}")
    print()
    
    # Call the transcription function with optional output_dir
    json_file_path = transcribe_conversation(audio_file, patient_id, doctor_id, output_directory)
    
    if json_file_path:
        print(f"\n✓ Success! Transcript saved to: {json_file_path}")
        
        # Display the contents of the created JSON file
        print("\nJSON Contents:")
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
    else:
        print("\n✗ Transcription failed. Check the logs above for details.")
        print("\nTo test this module, please:")
        print("1. Place an audio file in the project directory")
        print("2. Update the 'audio_file' variable with the correct path")
        print("3. Run the script again")
