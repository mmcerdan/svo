import requests
import sys

BASE = 'http://192.168.0.225:9010'
s = requests.Session()

# Login
print("=== LOGIN ===")
r = s.get(f'{BASE}/auth/login')
print(f'GET /auth/login: {r.status_code}')

# Extract CSRF token
csrf = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf = line.split('value="')[1].split('"')[0]
        break
print(f'CSRF token: {csrf[:20]}...' if csrf else 'CSRF: NOT FOUND')

r = s.post(f'{BASE}/auth/login', data={
    'usuario': 'admin',
    'senha': 'admin123',
    'csrf_token': csrf
}, allow_redirects=False)
print(f'POST /auth/login: {r.status_code} -> {r.headers.get("Location", "no redirect")}')

# Teste 1: Listar obitos
print("\n=== LISTAR OBITOS ===")
r = s.get(f'{BASE}/obitos/')
print(f'GET /obitos/: {r.status_code}')

# Teste 2: Detalhe obito (ID 1)
print("\n=== DETALHE OBITO ID=1 ===")
r = s.get(f'{BASE}/obitos/1')
print(f'GET /obitos/1: {r.status_code}')
if r.status_code != 200:
    # Extract error from page
    if '500' in r.text or 'Traceback' in r.text:
        print('  ERRO 500 detectado na pagina')

# Teste 3: Listar investigacoes
print("\n=== LISTAR INVESTIGACOES ===")
r = s.get(f'{BASE}/investigacoes/')
print(f'GET /investigacoes/: {r.status_code}')

# Teste 4: Detalhe investigacao (ID 1)
print("\n=== DETALHE INVESTIGACAO ID=1 ===")
r = s.get(f'{BASE}/investigacoes/1')
print(f'GET /investigacoes/1: {r.status_code}')
if r.status_code != 200:
    if '500' in r.text or 'Traceback' in r.text:
        print('  ERRO 500 detectado na pagina')

# Teste 5: Formulario nova investigacao para obito existente
print("\n=== NOVA INVESTIGACAO (OBITO ID=1) ===")
r = s.get(f'{BASE}/investigacoes/1/nova')
print(f'GET /investigacoes/1/nova: {r.status_code}')

# Teste 6: Imprimir investigacao
print("\n=== IMPRIMIR INVESTIGACAO ID=1 ===")
r = s.get(f'{BASE}/investigacoes/1/imprimir')
print(f'GET /investigacoes/1/imprimir: {r.status_code}')

# Teste 7: Editar investigacao
print("\n=== EDITAR INVESTIGACAO ID=1 ===")
r = s.get(f'{BASE}/investigacoes/1/editar')
print(f'GET /investigacoes/1/editar: {r.status_code}')

# Teste 8: Novo obito
print("\n=== NOVO OBITO (FORM) ===")
r = s.get(f'{BASE}/obitos/novo')
print(f'GET /obitos/novo: {r.status_code}')

# Teste 9: Editar obito
print("\n=== EDITAR OBITO ID=1 ===")
r = s.get(f'{BASE}/obitos/1/editar')
print(f'GET /obitos/1/editar: {r.status_code}')

# Teste 10: API campos por tipo
print("\n=== API CAMPOS POR TIPO (MATERNO) ===")
r = s.get(f'{BASE}/investigacoes/campos-por-tipo/MATERNO')
print(f'GET /investigacoes/campos-por-tipo/MATERNO: {r.status_code}')

print("\n=== DONE ===")
