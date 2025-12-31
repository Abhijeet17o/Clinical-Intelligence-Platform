import requests
url = 'http://127.0.0.1:5000/api/_debug/consultations'
try:
    r = requests.get(url, timeout=10)
    print(r.status_code)
    print(r.json())
except Exception as e:
    print('Error:', e)
