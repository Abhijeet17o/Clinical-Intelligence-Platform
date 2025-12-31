import os
import sys
import json
# Load .env
envpath = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(envpath):
    with open(envpath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if not API_KEY:
    print('No GEMINI/GOOGLE API key found in environment or .env')
    sys.exit(2)

audio_path = r"D:\ALL-CODE-HP\COLLEGE_STUFF\IPD PROJECT\v2\data\temp_audio\P20251115043736314C_20251226_232034.wav"
if not os.path.exists(audio_path):
    print('Audio file not found:', audio_path)
    sys.exit(3)

try:
    import google.generativeai as genai
except Exception as e:
    print('Import error for google.generativeai:', e)
    sys.exit(4)

# Configure
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print('Warning: genai.configure failed:', e)

print('Uploading audio (best-effort) ...')
uploaded = None
try:
    try:
        uploaded = genai.upload_file(audio_path)
    except Exception:
        uploaded = genai.upload_file(path=audio_path)
    print('Uploaded object:', type(uploaded), repr(uploaded)[:200])
except Exception as e:
    print('Upload failed:', e)

prompt = (
    "Transcribe this audio accurately. "
    "If multiple speakers are present, indicate speaker turns as Speaker 1/2 if possible. "
    "Return only the transcript text."
)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print('GenerativeModel creation failed:', e)
    sys.exit(5)

# Generation config
gen_cfg = None
try:
    gen_cfg = genai.GenerationConfig(temperature=0.0, max_output_tokens=32768)
except Exception:
    try:
        from google.generativeai import GenerationConfig
        gen_cfg = GenerationConfig(temperature=0.0, max_output_tokens=32768)
    except Exception:
        gen_cfg = None

contents = [prompt]
if uploaded is not None:
    contents.append(uploaded)
else:
    with open(audio_path, 'rb') as f:
        contents.append(f.read())

print('Calling model.generate_content ...')
try:
    if gen_cfg is not None:
        resp = model.generate_content(contents=contents, generation_config=gen_cfg)
    else:
        resp = model.generate_content(contents=contents)
except Exception as e:
    print('Model generate_content call failed:', e)
    sys.exit(6)

# Print raw response
print('\n--- RAW RESPONSE TYPE & repr ---')
print(type(resp))
try:
    from pprint import pformat
    print(pformat(resp.__dict__))
except Exception:
    print(repr(resp)[:1000])

print('\n--- Extracted fields ---')
text = getattr(resp, 'text', None)
output = getattr(resp, 'output', None)
candidates = getattr(resp, 'candidates', None)
print('text:', repr(text))
print('output:', repr(output))
print('candidates:', repr(candidates)[:400])

# If dict-like
if isinstance(resp, dict):
    print('\nRESP KEYS:', list(resp.keys()))
    if 'candidates' in resp:
        try:
            print('first candidate:', resp['candidates'][0])
        except Exception:
            pass

# Save to file for inspection
out_file = os.path.join('data', 'temp_audio', 'gemini_raw_response.json')
try:
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'repr': str(resp), 'text': text, 'output': output, 'candidates': str(candidates)}, f, indent=2)
    print('Saved partial response to', out_file)
except Exception as e:
    print('Failed to save response:', e)

# Print a simple transcript if present
transcript_text = text or (candidates[0].content if candidates else None) or (resp.get('text') if isinstance(resp, dict) else None)
print('\nEXTRACTED TRANSCRIPT:', repr(transcript_text))

if transcript_text:
    print('\nGemini produced transcript text.')
else:
    print('\nGemini did not return a usable transcript text.')
