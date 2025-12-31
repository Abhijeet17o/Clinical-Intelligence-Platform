import os
import sys
import importlib
# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['GEMINI_API_KEY'] = 'TEST_KEY_PLACEHOLDER'
# Reload module to recompute _USE_GEMINI
import modules.transcription_engine as te
importlib.reload(te)
print('_USE_GEMINI:', getattr(te, '_USE_GEMINI', None))

try:
    ret = te.transcribe_conversation('data/temp_audio/test_sine.wav', 'P005', 'DOC_TEST', output_dir='data/temp_audio')
    print('Transcription returned:', ret)
except Exception as e:
    print('Transcription raised an exception:')
    import traceback; traceback.print_exc()
