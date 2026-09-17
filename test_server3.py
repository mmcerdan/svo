import requests
import re
from html import unescape

BASE = 'http://192.168.0.225:9010'
s = requests.Session()

def get_csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if m:
        return unescape(m.group(1))
    m = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    if m:
        return unescape(m.group(1))
    return ''

# Login
r = s.get(f'{BASE}/auth/login')
csrf = get_csrf(r.text)
r = s.post(f'{BASE}/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf}, allow_redirects=False)
print(f'Login: {r.status_code}')

# ==========================================
# TESTE: Criar investigacao via POST
# ==========================================
print("\n=== CRIAR INVESTIGACAO ===")
r = s.get(f'{BASE}/investigacoes/1/nova')
csrf = get_csrf(r.text)
print(f'  GET form: {r.status_code}, CSRF: {csrf[:20]}...' if csrf else f'  GET form: {r.status_code}, CSRF: NOT FOUND')

r = s.post(f'{BASE}/investigacoes/1/nova', data={
    'csrf_token': csrf,
    'tipo': 'MATERNO',
    'status': 'EM_ANDAMENTO',
    'responsavel': 'Dr. Teste',
    'data_abertura': '2026-09-14',
}, allow_redirects=False)
print(f'  POST: {r.status_code} -> {r.headers.get("Location", "no redirect")}')
if r.status_code not in (302, 200):
    # Check for error details
    if 'Traceback' in r.text or 'Error' in r.text:
        err_match = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.DOTALL)
        if err_match:
            print(f'  Error detail: {err_match.group(1)[:300]}')

# ==========================================
# TESTE: Editar investigacao
# ==========================================
print("\n=== EDITAR INVESTIGACAO ===")
r = s.get(f'{BASE}/investigacoes/1/editar')
csrf = get_csrf(r.text)
print(f'  GET form: {r.status_code}, CSRF: {csrf[:20]}...' if csrf else f'  GET form: {r.status_code}, CSRF: NOT FOUND')

r = s.post(f'{BASE}/investigacoes/1/editar', data={
    'csrf_token': csrf,
    'tipo': 'MIF',
    'status': 'EM_ANDAMENTO',
    'responsavel': 'Dr. Teste Editado',
    'data_abertura': '2026-09-14',
}, allow_redirects=False)
print(f'  POST: {r.status_code} -> {r.headers.get("Location", "no redirect")}')
if r.status_code not in (302, 200):
    if 'Traceback' in r.text or 'Error' in r.text:
        err_match = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.DOTALL)
        if err_match:
            print(f'  Error detail: {err_match.group(1)[:300]}')

# ==========================================
# TESTE: Salvar campos
# ==========================================
print("\n=== SALVAR CAMPOS ===")
r = s.get(f'{BASE}/investigacoes/1')
csrf = get_csrf(r.text)

r = s.post(f'{BASE}/investigacoes/1/salvar-campos', data={
    'csrf_token': csrf,
}, allow_redirects=False)
print(f'  POST salvar-campos: {r.status_code}')
try:
    print(f'  Response: {r.json()}')
except:
    print(f'  Response: {r.text[:200]}')

# ==========================================
# TESTE: Finalizar
# ==========================================
print("\n=== FINALIZAR INVESTIGACAO ===")
r = s.get(f'{BASE}/investigacoes/1')
csrf = get_csrf(r.text)

r = s.post(f'{BASE}/investigacoes/1/finalizar', data={
    'csrf_token': csrf,
    'conclusao': 'Teste de conclusao',
}, allow_redirects=False)
print(f'  POST finalizar: {r.status_code} -> {r.headers.get("Location", "no redirect")}')
if r.status_code not in (302, 200):
    if 'Traceback' in r.text or 'Error' in r.text:
        err_match = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.DOTALL)
        if err_match:
            print(f'  Error detail: {err_match.group(1)[:300]}')

# ==========================================
# TESTE: Editar obito
# ==========================================
print("\n=== EDITAR OBITO ===")
r = s.get(f'{BASE}/obitos/1/editar')
csrf = get_csrf(r.text)
print(f'  GET form: {r.status_code}, CSRF: {csrf[:20]}...' if csrf else f'  GET form: {r.status_code}, CSRF: NOT FOUND')

r = s.post(f'{BASE}/obitos/1/editar', data={
    'csrf_token': csrf,
    'nome': 'Joao da Silva Teste',
    'data_nascimento': '1950-01-01',
    'data_obito': '2024-01-15',
    'sexo': 'M',
    'nome_mae': 'Maria da Silva',
    'numero_dob': 'DO-2024-0001',
    'causa_morte': 'Infarto',
    'causa_morte_cid': 'I21.9',
    'local_obito': 'HOSPITAL',
    'municipio_ocorrencia': 'Goianira',
}, allow_redirects=False)
print(f'  POST: {r.status_code} -> {r.headers.get("Location", "no redirect")}')
if r.status_code not in (302, 200):
    if 'Traceback' in r.text or 'Error' in r.text:
        err_match = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.DOTALL)
        if err_match:
            print(f'  Error detail: {err_match.group(1)[:300]}')

# ==========================================
# TESTE: PDF
# ==========================================
print("\n=== GERAR PDF ===")
r = s.get(f'{BASE}/investigacoes/1/pdf')
print(f'  GET pdf: {r.status_code}, Content-Type: {r.headers.get("Content-Type")}')
if r.status_code != 200 or 'html' in r.headers.get('Content-Type', ''):
    if 'Traceback' in r.text:
        err_match = re.search(r'<pre[^>]*>(.*?)</pre>', r.text, re.DOTALL)
        if err_match:
            print(f'  Error detail: {err_match.group(1)[:300]}')
    else:
        print(f'  Response: {r.text[:200]}')

print("\n=== DONE ===")
