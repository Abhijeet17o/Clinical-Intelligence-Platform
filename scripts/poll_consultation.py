import requests
import time
import sys

patient_id = 'P005'
url = f'http://127.0.0.1:5000/api/consultation_status/{patient_id}'
start = time.time()
print(f'Polling {url} for up to 60s...')
for i in range(40):
    try:
        r = requests.get(url, timeout=10)
        j = r.json()
        now = time.time()
        elapsed = now - start
        print(f'[{i}] elapsed={elapsed:.1f}s status={r.status_code} json_keys={list(j.keys())}')
        if j.get('success') and j.get('consultation'):
            proc = j['consultation'].get('processing')
            print('processing=', proc)
            if not proc:
                print('\n=== CONSULTATION COMPLETE ===')
                print('Consultation JSON:')
                import json
                print(json.dumps(j, indent=2))
                sys.exit(0)
    except Exception as e:
        print(f'[{i}] error: {e}')
    time.sleep(1.5)

print('Timed out waiting for consultation to complete')
try:
    r = requests.get(url, timeout=10)
    print('Final status:', r.status_code, r.text)
except Exception as e:
    print('Final fetch error:', e)
sys.exit(2)
