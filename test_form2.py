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

# Test: form page
r = s.get(f'{BASE}/investigacoes/1/nova')
print(f'Status: {r.status_code}')
print(f'URL: {r.url}')
# Find form elements
for i, line in enumerate(r.text.split('\n')):
    s_line = line.strip()
    if '<form' in s_line or '</form' in s_line or 'hidden_tag' in s_line or 'csrf' in s_line.lower() or 'Salvar' in s_line or 'method=' in s_line:
        print(f'  L{i}: {s_line[:200]}')

# Now test POST with CSRF from this form
csrf2 = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line:
        m = re.search(r'value="([^"]+)"', line)
        if m:
            csrf2 = unescape(m.group(1))
            break
print(f'\nCSRF from form: {csrf2[:30]}...' if csrf2 else '\nCSRF from form: NOT FOUND')

if csrf2:
    r = s.post(f'{BASE}/investigacoes/1/nova', data={
        'csrf_token': csrf2,
        'tipo': 'MATERNO',
        'status': 'EM_ANDAMENTO',
        'responsavel': 'Dr. Teste',
        'data_abertura': '2026-09-14',
    }, allow_redirects=False)
    print(f'POST /investigacoes/1/nova: {r.status_code} -> {r.headers.get("Location", "no redirect")}')
    if r.status_code not in (302,):
        # Show the page content if not redirect
        for i, line in enumerate(r.text.split('\n')):
            if 'error' in line.lower() or 'erro' in line.lower() or 'flash' in line.lower() or 'danger' in line.lower() or 'success' in line.lower():
                print(f'  L{i}: {line.strip()[:200]}')
