import requests
import re
from html import unescape

BASE = 'http://192.168.0.225:9010'
s = requests.Session()

def get_csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if m: return unescape(m.group(1))
    m = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    if m: return unescape(m.group(1))
    return ''

# Login
r = s.get(f'{BASE}/auth/login')
csrf = get_csrf(r.text)
r = s.post(f'{BASE}/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf}, allow_redirects=True)
print(f'Login: {r.status_code}, URL: {r.url}')

# ==========================================
# TESTE 1: Detalhe obito
# ==========================================
print("\n=== 1. DETALHE OBITO ID=1 ===")
r = s.get(f'{BASE}/obitos/1')
print(f'Status: {r.status_code}')

# ==========================================
# TESTE 2: Criar investigacao GET form
# ==========================================
print("\n=== 2. NOVA INVESTIGACAO (GET) ===")
r = s.get(f'{BASE}/investigacoes/1/nova')
print(f'Status: {r.status_code}, URL: {r.url}')
csrf = get_csrf(r.text)
print(f'CSRF: {csrf[:30]}...' if csrf else 'CSRF: NOT FOUND')

# ==========================================
# TESTE 3: Criar investigacao POST
# ==========================================
print("\n=== 3. CRIAR INVESTIGACAO (POST) ===")
if csrf:
    r = s.post(f'{BASE}/investigacoes/1/nova', data={
        'csrf_token': csrf,
        'tipo': 'MATERNO',
        'status': 'EM_ANDAMENTO',
        'responsavel': 'Dr. Teste Auditing',
        'data_abertura': '2026-09-14',
    }, allow_redirects=True)
    print(f'Status: {r.status_code}, URL: {r.url}')
    # Check for flash messages
    for line in r.text.split('\n'):
        if 'flash' in line.lower() or 'alert-success' in line or 'alert-danger' in line:
            print(f'  Flash: {line.strip()[:150]}')

# ==========================================
# TESTE 4: Listar investigacoes
# ==========================================
print("\n=== 4. LISTAR INVESTIGACOES ===")
r = s.get(f'{BASE}/investigacoes/')
print(f'Status: {r.status_code}')

# ==========================================
# TESTE 5: Detalhe investigacao
# ==========================================
print("\n=== 5. DETALHE INVESTIGACAO ID=1 ===")
r = s.get(f'{BASE}/investigacoes/1')
print(f'Status: {r.status_code}')

# ==========================================
# TESTE 6: Editar investigacao GET
# ==========================================
print("\n=== 6. EDITAR INVESTIGACAO ID=1 (GET) ===")
r = s.get(f'{BASE}/investigacoes/1/editar')
print(f'Status: {r.status_code}, URL: {r.url}')
csrf = get_csrf(r.text)

# ==========================================
# TESTE 7: Editar investigacao POST
# ==========================================
print("\n=== 7. EDITAR INVESTIGACAO ID=1 (POST) ===")
if csrf:
    r = s.post(f'{BASE}/investigacoes/1/editar', data={
        'csrf_token': csrf,
        'tipo': 'MIF',
        'status': 'EM_ANDAMENTO',
        'responsavel': 'Dr. Editado',
        'data_abertura': '2026-09-14',
    }, allow_redirects=True)
    print(f'Status: {r.status_code}, URL: {r.url}')
    for line in r.text.split('\n'):
        if 'alert-success' in line or 'alert-danger' in line:
            print(f'  Flash: {line.strip()[:150]}')

# ==========================================
# TESTE 8: Salvar campos
# ==========================================
print("\n=== 8. SALVAR CAMPOS ===")
r = s.get(f'{BASE}/investigacoes/1')
csrf = get_csrf(r.text)
if csrf:
    r = s.post(f'{BASE}/investigacoes/1/salvar-campos', data={
        'csrf_token': csrf,
    })
    print(f'Status: {r.status_code}')
    try:
        print(f'Response: {r.json()}')
    except:
        print(f'Response: {r.text[:200]}')

# ==========================================
# TESTE 9: Finalizar
# ==========================================
print("\n=== 9. FINALIZAR ===")
r = s.get(f'{BASE}/investigacoes/1')
csrf = get_csrf(r.text)
if csrf:
    r = s.post(f'{BASE}/investigacoes/1/finalizar', data={
        'csrf_token': csrf,
        'conclusao': 'Teste de conclusao via auditing',
    }, allow_redirects=True)
    print(f'Status: {r.status_code}, URL: {r.url}')

# ==========================================
# TESTE 10: Imprimir
# ==========================================
print("\n=== 10. IMPRIMIR ===")
r = s.get(f'{BASE}/investigacoes/1/imprimir')
print(f'Status: {r.status_code}')

# ==========================================
# TESTE 11: PDF
# ==========================================
print("\n=== 11. PDF ===")
r = s.get(f'{BASE}/investigacoes/1/pdf')
print(f'Status: {r.status_code}, Content-Type: {r.headers.get("Content-Type")}')
if r.status_code != 200 or 'html' in r.headers.get('Content-Type', ''):
    for line in r.text.split('\n'):
        if 'error' in line.lower() or 'traceback' in line.lower():
            print(f'  Error: {line.strip()[:200]}')

# ==========================================
# TESTE 12: Editar obito
# ==========================================
print("\n=== 12. EDITAR OBITO ID=1 ===")
r = s.get(f'{BASE}/obitos/1/editar')
print(f'Status: {r.status_code}')
csrf = get_csrf(r.text)
if csrf:
    r = s.post(f'{BASE}/obitos/1/editar', data={
        'csrf_token': csrf,
        'nome': 'Joao da Silva Auditado',
        'data_nascimento': '1950-01-01',
        'data_obito': '2024-01-15',
        'sexo': 'M',
        'nome_mae': 'Maria da Silva',
        'numero_dob': 'DO-2024-0001',
        'causa_morte': 'Infarto',
        'causa_morte_cid': 'I21.9',
        'local_obito': 'HOSPITAL',
        'municipio_ocorrencia': 'Goianira',
    }, allow_redirects=True)
    print(f'Status: {r.status_code}, URL: {r.url}')

print("\n=== DONE ===")
