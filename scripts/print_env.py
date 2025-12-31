import os
print('GEMINI_API_KEY present:' , bool(os.environ.get('GEMINI_API_KEY')))
print('GEMINI_API_KEY:', os.environ.get('GEMINI_API_KEY') and os.environ.get('GEMINI_API_KEY')[:6] + '...')
