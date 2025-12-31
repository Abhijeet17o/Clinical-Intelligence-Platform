import sys
import os
import traceback
# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import transcription_engine

audio = 'data/temp_audio/test_sine.wav'
try:
    print('Calling transcribe_conversation...')
    out = transcription_engine.transcribe_conversation(audio, 'P005', 'DOC_TEST', output_dir='data/temp_audio')
    print('Result:', out)
except Exception as e:
    print('Error during transcription:')
    traceback.print_exc()
