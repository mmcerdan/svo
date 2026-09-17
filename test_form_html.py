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

# Check nova investigacao form HTML
r = s.get(f'{BASE}/investigacoes/1/nova')
print(f'GET /investigacoes/1/nova: {r.status_code}')
print('--- FORM CONTENT (relevant lines) ---')
for i, line in enumerate(r.text.split('\n')):
    line_s = line.strip()
    if 'csrf' in line_s.lower() or 'form' in line_s.lower() or 'input' in line_s.lower() or 'method' in line_s.lower():
        print(f'  L{i}: {line_s[:200]}')

# Check detalhe page HTML
print('\n--- DETALHE PAGE ---')
r = s.get(f'{BASE}/investigacoes/1')
for i, line in enumerate(r.text.split('\n')):
    line_s = line.strip()
    if 'csrf' in line_s.lower() or 'form' in line_s.lower() or 'salvar' in line_s.lower():
        print(f'  L{i}: {line_s[:200]}')
