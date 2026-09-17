import requests

BASE = 'http://192.168.0.225:9010'
s = requests.Session()

# Login com verbose
print("=== STEP 1: Get login page ===")
r = s.get(f'{BASE}/auth/login')
print(f'Status: {r.status_code}, URL: {r.url}')
print(f'Cookies after GET: {dict(s.cookies)}')

# Extract CSRF
import re
from html import unescape
csrf = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line:
        m = re.search(r'value="([^"]+)"', line)
        if m:
            csrf = unescape(m.group(1))
            break
print(f'CSRF: {csrf[:30]}...' if csrf else 'CSRF: NOT FOUND')

print("\n=== STEP 2: POST login ===")
r = s.post(f'{BASE}/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf}, allow_redirects=True)
print(f'Status: {r.status_code}, Final URL: {r.url}')
print(f'Cookies after POST: {dict(s.cookies)}')

print("\n=== STEP 3: Access /investigacoes/1/nova ===")
r = s.get(f'{BASE}/investigacoes/1/nova', allow_redirects=False)
print(f'Status: {r.status_code}, Location: {r.headers.get("Location", "none")}')
print(f'Final URL: {r.url}')

print("\n=== STEP 4: Access /obitos/ ===")
r = s.get(f'{BASE}/obitos/')
print(f'Status: {r.status_code}')

print("\n=== STEP 5: Check if session is valid by accessing /obitos/1 ===")
r = s.get(f'{BASE}/obitos/1', allow_redirects=False)
print(f'Status: {r.status_code}, Location: {r.headers.get("Location", "none")}')
