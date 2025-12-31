import importlib, inspect

genai = importlib.import_module('google.generativeai')
print('genai members:', [m for m in dir(genai) if not m.startswith('_')])
if hasattr(genai, 'GenerativeModel'):
    print('GenerativeModel available')
    print('signature of generate_content:', inspect.signature(genai.GenerativeModel.generate_content))
    print('doc:', genai.GenerativeModel.generate_content.__doc__)
else:
    print('GenerativeModel not found')
