import numpy as np
import soundfile as sf
import os

os.makedirs('data/temp_audio', exist_ok=True)
file_path = os.path.join('data', 'temp_audio', 'test_sine.wav')
fs = 16000
duration = 2.0
f = 440.0
t = np.linspace(0, duration, int(fs*duration), endpoint=False)
wave = 0.2 * np.sin(2 * np.pi * f * t)
sf.write(file_path, wave, fs)
print(f"Wrote test audio to: {file_path}")
