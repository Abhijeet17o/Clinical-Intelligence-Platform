import importlib, inspect

genai = importlib.import_module('google.generativeai')
print('members:', [m for m in dir(genai) if 'upload' in m or 'file' in m])
if hasattr(genai, 'upload_file'):
    print('upload_file sig:', inspect.signature(genai.upload_file))
    print('doc:', genai.upload_file.__doc__[:400])
if hasattr(genai, 'upload_file'):
    print('upload_file exists')
else:
    print('no upload_file')
