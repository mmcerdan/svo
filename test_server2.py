import requests
import json

BASE = 'http://192.168.0.225:9010'
s = requests.Session()

# Login
r = s.get(f'{BASE}/auth/login')
csrf = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf = line.split('value="')[1].split('"')[0]
        break
r = s.post(f'{BASE}/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf}, allow_redirects=False)

# ==========================================
# TESTE 1: Criar investigacao via formulario
# ==========================================
print("=== CRIAR INVESTIGACAO (POST) ===")
r = s.get(f'{BASE}/investigacoes/1/nova')
csrf2 = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf2 = line.split('value="')[1].split('"')[0]
        break

r = s.post(f'{BASE}/investigacoes/1/nova', data={
    'csrf_token': csrf2,
    'tipo': 'MATERNO',
    'status': 'EM_ANDAMENTO',
    'responsavel': 'Dr. Teste',
    'data_abertura': '2026-09-14',
}, allow_redirects=False)
print(f'POST /investigacoes/1/nova: {r.status_code} -> {r.headers.get("Location", "no redirect")}')

# ==========================================
# TESTE 2: Editar investigacao (GET form)
# ==========================================
print("\n=== EDITAR INVESTIGACAO (GET form) ===")
r = s.get(f'{BASE}/investigacoes/1/editar')
print(f'GET /investigacoes/1/editar: {r.status_code}')
csrf3 = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf3 = line.split('value="')[1].split('"')[0]
        break

# ==========================================
# TESTE 3: Editar investigacao (POST update)
# ==========================================
print("\n=== EDITAR INVESTIGACAO (POST update) ===")
r = s.post(f'{BASE}/investigacoes/1/editar', data={
    'csrf_token': csrf3,
    'tipo': 'MIF',
    'status': 'EM_ANDAMENTO',
    'responsavel': 'Dr. Teste Editado',
    'data_abertura': '2026-09-14',
}, allow_redirects=False)
print(f'POST /investigacoes/1/editar: {r.status_code} -> {r.headers.get("Location", "no redirect")}')

# ==========================================
# TESTE 4: Salvar campos (AJAX)
# ==========================================
print("\n=== SALVAR CAMPOS (AJAX POST) ===")
# First get the detail to find campo IDs
r = s.get(f'{BASE}/investigacoes/1')
csrf4 = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf4 = line.split('value="')[1].split('"')[0]
        break

# Try saving with form data
r = s.post(f'{BASE}/investigacoes/1/salvar-campos', data={
    'csrf_token': csrf4,
    'campo_1': 'Teste valor',
}, allow_redirects=False)
print(f'POST /investigacoes/1/salvar-campos: {r.status_code}')
print(f'  Content-Type: {r.headers.get("Content-Type")}')
try:
    resp = r.json()
    print(f'  Response: {resp}')
except:
    print(f'  Response text (first 200 chars): {r.text[:200]}')

# ==========================================
# TESTE 5: Finalizar investigacao
# ==========================================
print("\n=== FINALIZAR INVESTIGACAO (POST) ===")
r = s.post(f'{BASE}/investigacoes/1/finalizar', data={
    'csrf_token': csrf4,
    'conclusao': 'Investigacao concluida com sucesso via teste.',
}, allow_redirects=False)
print(f'POST /investigacoes/1/finalizar: {r.status_code} -> {r.headers.get("Location", "no redirect")}')

# ==========================================
# TESTE 6: PDF
# ==========================================
print("\n=== GERAR PDF ===")
r = s.get(f'{BASE}/investigacoes/1/pdf')
print(f'GET /investigacoes/1/pdf: {r.status_code}')
print(f'  Content-Type: {r.headers.get("Content-Type")}')
if r.status_code != 200:
    print(f'  Error: {r.text[:300]}')

# ==========================================
# TESTE 7: Criar novo obito
# ==========================================
print("\n=== CRIAR NOVO OBITO (POST) ===")
r = s.get(f'{BASE}/obitos/novo')
csrf5 = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf5 = line.split('value="')[1].split('"')[0]
        break

r = s.post(f'{BASE}/obitos/novo', data={
    'csrf_token': csrf5,
    'nome': 'Maria Teste Silva',
    'data_nascimento': '1990-05-15',
    'data_obito': '2026-09-10',
    'sexo': 'F',
    'nome_mae': 'Joana Silva',
    'numero_dob': 'DO-TEST-001',
    'causa_morte': 'Causa teste',
    'causa_morte_cid': 'A00',
    'local_obito': 'HOSPITAL',
    'municipio_ocorrencia': 'Goianira',
    'criar_investigacao': 'MIF',
}, allow_redirects=False)
print(f'POST /obitos/novo: {r.status_code} -> {r.headers.get("Location", "no redirect")}')

# ==========================================
# TESTE 8: Editar obito
# ==========================================
print("\n=== EDITAR OBITO ID=1 (POST) ===")
r = s.get(f'{BASE}/obitos/1/editar')
csrf6 = ''
for line in r.text.split('\n'):
    if 'csrf_token' in line and 'value=' in line:
        csrf6 = line.split('value="')[1].split('"')[0]
        break

r = s.post(f'{BASE}/obitos/1/editar', data={
    'csrf_token': csrf6,
    'nome': 'Joao da Silva Editado',
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
print(f'POST /obitos/1/editar: {r.status_code} -> {r.headers.get("Location", "no redirect")}')

# ==========================================
# TESTE 9: API campos por tipo
# ==========================================
print("\n=== API CAMPOS POR TIPO ===")
for tipo in ['MIF', 'MATERNO', 'INFANTIL_FETAL', 'MAL_DEFINIDA', 'INFANTIL']:
    r = s.get(f'{BASE}/investigacoes/campos-por-tipo/{tipo}')
    print(f'GET /investigacoes/campos-por-tipo/{tipo}: {r.status_code}')
    if r.status_code != 200:
        print(f'  Error: {r.text[:200]}')

print("\n=== DONE ===")
