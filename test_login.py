import requests
import re
from html import unescape

BASE = 'http://192.168.0.225:9010'
s = requests.Session()

# Login
r = s.get(f'{BASE}/auth/login')
csrf = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line:
        m = re.search(r'value="([^"]+)"', line)
        if m:
            csrf = unescape(m.group(1))
            break

r = s.post(f'{BASE}/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf}, allow_redirects=False)
print(f'Login status: {r.status_code}')
print(f'Location: {r.headers.get("Location", "none")}')

# Check for flash messages in response
if r.status_code == 200:
    # Login stayed on same page - error
    r2 = s.get(f'{BASE}/auth/login')
    for i, line in enumerate(r2.text.split('\n')):
        if 'flash' in line.lower() or 'alert' in line.lower() or 'danger' in line.lower() or 'error' in line.lower():
            print(f'L{i}: {line.strip()[:200]}')

# Follow redirect to see if we're logged in
if r.status_code == 302:
    r = s.get(f'{BASE}{r.headers["Location"]}')
    print(f'After redirect: {r.status_code}, URL: {r.url}')
    for i, line in enumerate(r.text.split('\n')):
        if 'logout' in line.lower() or 'sair' in line.lower() or 'admin' in line.lower():
            print(f'  L{i}: {line.strip()[:200]}')
            break
