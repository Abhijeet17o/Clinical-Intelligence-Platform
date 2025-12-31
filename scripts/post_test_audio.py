import requests
import os
import time

url = 'http://127.0.0.1:5000/api/process_consultation_v2/P005'
files = {'audio': open('data/temp_audio/test_sine.wav', 'rb')}

print(f"Posting to {url}...")
for i in range(3):
    try:
        resp = requests.post(url, files=files, timeout=30)
        print(f"Status: {resp.status_code}")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
        break
    except Exception as e:
        print(f"Attempt {i+1} failed: {e}")
        time.sleep(1)
else:
    print("All attempts failed")
