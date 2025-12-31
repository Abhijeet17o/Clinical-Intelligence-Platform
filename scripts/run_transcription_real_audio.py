import os,sys,importlib
# Load .env
envpath = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(envpath):
    with open(envpath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k,v = line.split('=',1)
                os.environ.setdefault(k.strip(), v.strip())

# Ensure project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import modules.transcription_engine as te
importlib.reload(te)
print('_USE_GEMINI =', getattr(te, '_USE_GEMINI', None))

audio = os.path.join('data', 'temp_audio', 'P20251115043736314C_20251226_232034.wav')
if not os.path.exists(audio):
    print('Audio missing:', audio)
    sys.exit(3)

try:
    out = te.transcribe_conversation(audio, 'P20251115043736314C', 'DOC_TEST', output_dir='data/temp_audio')
    print('Transcription returned:', out)
except Exception as e:
    print('Transcription raised exception:')
    import traceback; traceback.print_exc()
