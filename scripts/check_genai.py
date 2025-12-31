import importlib
try:
    genai = importlib.import_module('google.generativeai')
    print('genai imported:', getattr(genai, '__version__', 'unknown'))
except Exception as e:
    print('genai import failed:', e)
