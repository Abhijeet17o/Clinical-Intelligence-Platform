"""
Audio Recording Module
This module allows recording audio from the microphone via terminal
and saves it as an audio file for use with the transcription module.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def record_audio(duration=None, sample_rate=44100, channels=1, output_dir='recordings'):
    """
    Records audio from the microphone and saves it to a file.
    
    Args:
        duration (int, optional): Recording duration in seconds. 
                                  If None, records until user presses Enter.
        sample_rate (int): Sample rate in Hz (default: 44100)
        channels (int): Number of audio channels (1=mono, 2=stereo, default: 1)
        output_dir (str): Directory to save the audio file
    
    Returns:
        str: Path to the saved audio file, or None if recording fails
    """
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(output_dir, filename)
        
        logger.info(f"Recording audio...")
        logger.info(f"Sample rate: {sample_rate} Hz")
        logger.info(f"Channels: {channels}")
        
        if duration:
            logger.info(f"Recording for {duration} seconds...")
            print(f"\n🎤 Recording for {duration} seconds... Speak now!")
            
            # Record for specified duration
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                dtype='float32'
            )
            sd.wait()  # Wait until recording is finished
            
        else:
            logger.info("Recording until you press Enter...")
            print("\n🎤 Recording started... Press ENTER to stop recording.")
            
            # Start recording in the background
            recording = sd.rec(
                int(300 * sample_rate),  # Max 5 minutes
                samplerate=sample_rate,
                channels=channels,
                dtype='float32'
            )
            
            # Wait for user to press Enter
            input()
            
            # Stop recording
            sd.stop()
            
            # Get only the recorded portion
            current_frame = sd.get_stream().write_available
            audio_data = recording[:len(recording) - current_frame]
        
        print("✓ Recording stopped.")
        
        # Save the recording to a WAV file
        logger.info(f"Saving audio to: {filepath}")
        sf.write(filepath, audio_data, sample_rate)
        
        logger.info(f"Audio saved successfully!")
        print(f"✓ Audio saved to: {filepath}")
        
        return filepath
    
    except Exception as e:
        logger.error(f"Error during audio recording: {e}", exc_info=True)
        print(f"✗ Recording failed: {e}")
        return None


def record_with_custom_settings():
    """
    Interactive function to record audio with custom settings.
    
    Returns:
        str: Path to the saved audio file, or None if recording fails
    """
    
    print("="*60)
    print("Audio Recording Module")
    print("="*60)
    print("\nConfigure your recording settings:")
    
    try:
        # Get recording duration
        duration_input = input("\nEnter recording duration in seconds (or press Enter for manual stop): ").strip()
        duration = int(duration_input) if duration_input else None
        
        # Get sample rate
        print("\nSample rate options:")
        print("  1. 16000 Hz (Good for speech, smaller file)")
        print("  2. 44100 Hz (CD quality, default)")
        print("  3. 48000 Hz (Professional quality)")
        
        sample_rate_choice = input("Choose (1/2/3) [default: 2]: ").strip()
        sample_rates = {'1': 16000, '2': 44100, '3': 48000}
        sample_rate = sample_rates.get(sample_rate_choice, 44100)
        
        # Get channels
        channels_input = input("\nChannels (1=mono, 2=stereo) [default: 1]: ").strip()
        channels = int(channels_input) if channels_input and channels_input in ['1', '2'] else 1
        
        # Get output directory
        output_dir = input("\nOutput directory [default: recordings]: ").strip()
        output_dir = output_dir if output_dir else 'recordings'
        
        # Record audio
        return record_audio(duration, sample_rate, channels, output_dir)
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print(f"✗ Invalid input. Please enter valid numbers.")
        return None
    except Exception as e:
        logger.error(f"Error in interactive recording: {e}", exc_info=True)
        print(f"✗ Recording failed: {e}")
        return None


def quick_record(duration=30, output_dir='recordings'):
    """
    Quick record function with default settings (30 seconds, mono, 16kHz).
    
    Args:
        duration (int): Recording duration in seconds (default: 30)
        output_dir (str): Directory to save the audio file
    
    Returns:
        str: Path to the saved audio file, or None if recording fails
    """
    print("="*60)
    print("Quick Audio Recording (30 seconds, optimized for speech)")
    print("="*60)
    
    return record_audio(duration=duration, sample_rate=16000, channels=1, output_dir=output_dir)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Audio Recording Module - Choose Recording Mode")
    print("="*60)
    print("\n1. Quick Record (30 seconds, speech optimized)")
    print("2. Custom Recording (configure settings)")
    print("3. Press Enter to Stop (manual control)")
    
    choice = input("\nEnter your choice (1/2/3) [default: 1]: ").strip()
    
    audio_file = None
    
    if choice == '2':
        # Custom recording with user-defined settings
        audio_file = record_with_custom_settings()
    elif choice == '3':
        # Manual stop recording
        print("\n" + "="*60)
        print("Manual Recording Mode")
        print("="*60)
        audio_file = record_audio(duration=None, sample_rate=16000, channels=1)
    else:
        # Quick record (default)
        audio_file = quick_record()
    
    # If recording was successful, offer to transcribe
    if audio_file:
        print("\n" + "="*60)
        print("Recording Complete!")
        print("="*60)
        print(f"\nYou can now use this file with the transcription module:")
        print(f"  File: {audio_file}")
        
        # Ask if user wants to transcribe now
        transcribe_now = input("\nWould you like to transcribe this recording now? (y/n): ").strip().lower()
        
        if transcribe_now == 'y':
            try:
                # Import and use the transcription module
                import transcription_module
                
                patient_id = input("Enter Patient ID: ").strip()
                doctor_id = input("Enter Doctor ID: ").strip()
                
                print("\nStarting transcription...")
                json_path = transcription_module.transcribe_conversation(
                    audio_file, 
                    patient_id, 
                    doctor_id,
                    output_dir='transcripts'
                )
                
                if json_path:
                    print(f"\n✓ Transcription completed successfully!")
                    print(f"  Transcript saved to: {json_path}")
                else:
                    print("\n✗ Transcription failed. Check the logs for details.")
                    
            except ImportError:
                print("\n⚠ Transcription module not found.")
                print("Please ensure 'transcription_module.py' is in the same directory.")
            except Exception as e:
                print(f"\n✗ Error during transcription: {e}")
