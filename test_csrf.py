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
        print(f'CSRF LINE: {line.strip()}')
        m = re.search(r'value="([^"]+)"', line)
        if m:
            csrf = unescape(m.group(1))
            break

r = s.post(f'{BASE}/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf}, allow_redirects=False)
print(f'Login: {r.status_code}')

# Check form HTML for CSRF
r = s.get(f'{BASE}/investigacoes/1/nova')
# Find ALL hidden inputs
for line in r.text.split('\n'):
    if 'hidden' in line.lower() or 'csrf' in line.lower():
        print(f'HIDDEN: {line.strip()[:200]}')

# Check cookies
print(f'\nCookies: {dict(s.cookies)}')

# Try without CSRF to see the error
r = s.post(f'{BASE}/investigacoes/1/salvar-campos', data={}, allow_redirects=False)
print(f'\nSalvar campos sem CSRF: {r.status_code}')
print(f'Response: {r.text[:300]}')
