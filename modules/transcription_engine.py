"""
Module 1: Transcription Engine
This module transcribes doctor-patient conversations using OpenAI's Whisper model
and saves the transcript to a structured JSON file.
"""

import json
import os
import logging
from datetime import datetime

# Try to import Gemini client (google.generativeai); if not available we'll fall back to local Whisper
try:
    import google.generativeai as genai
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False

from modules.utils.perf import Timer, get_records

_USE_GEMINI = bool(os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')) and _HAS_GEMINI

# Attempt to import local Whisper for fallback (optional) regardless of Gemini availability
try:
    import whisper
except Exception:
    whisper = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import shutil
import subprocess

def reencode_audio_to_mono16k(source_path: str) -> str:
    """Re-encode audio to mono 16kHz WAV using ffmpeg if available.

    Returns the path to the re-encoded file (may be the original if ffmpeg not available or if re-encode fails).
    """
    try:
        ffmpeg_exe = shutil.which('ffmpeg')
        if not ffmpeg_exe:
            logger.debug('ffmpeg not found in PATH, skipping re-encode')
            return source_path

        base, ext = os.path.splitext(source_path)
        out_path = f"{base}_16k_mono.wav"
        cmd = [ffmpeg_exe, '-y', '-i', source_path, '-ac', '1', '-ar', '16000', '-vn', '-acodec', 'pcm_s16le', out_path]
        logger.info(f'Re-encoding audio to mono 16kHz WAV: {out_path}')
        subprocess.run(cmd, check=True)
        return out_path
    except Exception as e:
        logger.warning(f'Audio re-encode failed, using original file: {e}')
        return source_path


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

        # Gemini-only mode: require GEMINI API key and use Gemini for transcription only.
        if _USE_GEMINI:
            api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

            # Configure genai and create GenerativeModel
            try:
                genai.configure(api_key=api_key)
            except Exception as e:
                logger.debug(f"genai.configure not available or failed: {e}")

            logger.info("Using Gemini API for transcription (gemini-2.5-flash) [Gemini-only mode]")

            # Build prompt for transcription
            prompt = (
                "Transcribe this audio accurately. "
                "If multiple speakers are present, indicate speaker turns as Speaker 1/2 if possible. "
                "Return only the transcript text."
            )

            # Re-encode audio to mono 16kHz WAV if possible to reduce upload time
            try:
                audio_to_upload = reencode_audio_to_mono16k(audio_file_path)
            except Exception:
                audio_to_upload = audio_file_path

            # Upload audio (best-effort)
            uploaded = None
            try:
                with Timer('upload_audio'):
                    try:
                        uploaded = genai.upload_file(audio_to_upload)
                    except Exception:
                        uploaded = genai.upload_file(path=audio_to_upload)
                logger.info("Uploaded audio to Gemini Files API")
            except Exception as e:
                logger.error(f"Could not upload audio via genai.upload_file: {e}")
                # Fail fast in Gemini-only mode
                raise RuntimeError("Gemini file upload failed")

            # Instantiate model
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                logger.error(f"GenerativeModel API unavailable: {e}")
                raise RuntimeError("Gemini GenerativeModel API is not available")

            # Prepare contents
            contents = [prompt, uploaded]

            # Use GenerationConfig for deterministic transcription
            gen_cfg = None
            try:
                gen_cfg = genai.GenerationConfig(temperature=0.0, max_output_tokens=32768)
            except Exception:
                try:
                    from google.generativeai import GenerationConfig
                    gen_cfg = GenerationConfig(temperature=0.0, max_output_tokens=32768)
                except Exception:
                    gen_cfg = None

            # Call Gemini and fail fast on any error or empty result
            try:
                with Timer('gemini_generate'):
                    if gen_cfg is not None:
                        response = model.generate_content(contents=contents, generation_config=gen_cfg)
                    else:
                        response = model.generate_content(contents=contents)

                # Parse response
                with Timer('parse_transcript'):
                    transcript_text = getattr(response, 'text', None) or getattr(response, 'output', None)

                    # Handle candidate-style responses (list of candidate objects)
                    if not transcript_text and hasattr(response, 'candidates'):
                        try:
                            transcript_text = response.candidates[0].content if response.candidates else None
                        except Exception:
                            transcript_text = None

                    # Handle dict-like responses or objects exposing .get()
                    if not transcript_text and hasattr(response, 'get') and callable(getattr(response, 'get')):
                        try:
                            transcript_text = response.get('text') or response.get('output')
                            if not transcript_text:
                                candidates = response.get('candidates')
                                if candidates:
                                    first = candidates[0]
                                    if isinstance(first, dict):
                                        transcript_text = first.get('content') or first.get('text')
                                    else:
                                        transcript_text = getattr(first, 'content', None) or getattr(first, 'text', None)
                        except Exception:
                            transcript_text = None

                    transcript_text = (transcript_text or "").strip()

                    if not transcript_text:
                        logger.error("Gemini returned empty transcript in Gemini-only mode")
                        raise RuntimeError("Empty transcript from Gemini")

                result = {"text": transcript_text}

                # Attach perf timing summary to the transcript data when writing
                try:
                    perf_list = get_records(reset=True)
                    perf_obj = {name: round(sec, 3) for name, sec in perf_list}
                    # Save perf object in the result dictionary so it's persisted
                    result['_perf'] = perf_obj
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Gemini transcription failed: {e}", exc_info=True)
                # Fail-fast: do not fallback to Whisper in Gemini-only mode
                raise

        else:
            if whisper is None:
                raise RuntimeError("Whisper is not installed and no Gemini API key found")

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
            "transcript": result.get("text") if isinstance(result, dict) else (result["text"] if isinstance(result, dict) else result)
        }

        # If we have performance data attached to the result (from Timer), persist it
        try:
            if isinstance(result, dict) and '_perf' in result:
                transcript_data['_perf'] = result['_perf']
        except Exception:
            pass
        
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
