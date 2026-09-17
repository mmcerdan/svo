import sys
sys.path.insert(0, '/opt/sistema-obito')
from app import create_app
from app.extensions import db
from app.models import Investigacao

app = create_app()

with app.test_client() as client:
    import re
    from html import unescape
    
    # Login
    r = client.get('/auth/login')
    csrf = ''
    for line in r.data.decode().split('\n'):
        if 'csrf_token' in line:
            m = re.search(r'value="([^"]+)"', line)
            if m:
                csrf = unescape(m.group(1))
                break
    r = client.post('/auth/login', data={'usuario': 'admin', 'senha': 'admin123', 'csrf_token': csrf})
    
    # API campos-por-tipo INFANTIL_FETAL
    r = client.get('/investigacoes/campos-por-tipo/INFANTIL_FETAL')
    data = r.get_json()
    
    # Verificar grupos Lista Brasileira
    for grupo in data.get('grupos', []):
        if grupo['tipo'] == 'grupo' and 'Lista Brasileira' in grupo['titulo']:
            print(f'Grupo: {grupo["titulo"]} - {len(grupo["campos"])} opções')
            for c in grupo['campos']:
                print(f'  - {c["nome"]}')
    
    # Verificar Recomendacao
    for grupo in data.get('grupos', []):
        if grupo['tipo'] == 'grupo' and 'Recomendacao' in grupo['titulo']:
            print(f'Grupo: {grupo["titulo"]} - {len(grupo["campos"])} opções')
            for c in grupo['campos']:
                print(f'  - {c["nome"]}')
    
    # Testar renderização no frontend
    r = client.post('/investigacoes/1/nova', data={
        'csrf_token': csrf,
        'tipo': 'INFANTIL_FETAL',
        'status': 'EM_ANDAMENTO',
        'responsavel': 'Teste LB',
        'data_abertura': '2026-09-14',
    }, follow_redirects=True)
    
    new_inv = db.session.query(Investigacao).filter_by(tipo='INFANTIL_FETAL').order_by(Investigacao.id.desc()).first()
    if new_inv:
        r = client.get(f'/investigacoes/{new_inv.id}')
        html = r.data.decode()
        
        # Procurar Lista Brasileira
        lb_count = len(re.findall(r'Lista Brasileira', html))
        print(f'\nOcorrências "Lista Brasileira" no HTML: {lb_count}')
        
        # Procurar Recomendacao
        rec_count = len(re.findall(r'Recomendacao', html))
        print(f'Ocorrências "Recomendacao" no HTML: {rec_count}')
        
        # Verificar títulos duplicados
        titulo_matches = re.findall(r'grupo-titulo">([^<]+)</div>', html)
        titulo_counts = {}
        for t in titulo_matches:
            if 'Lista Brasileira' in t or 'Recomendacao' in t:
                titulo_counts[t] = titulo_counts.get(t, 0) + 1
        for t, c in titulo_counts.items():
            print(f'{c}x: {t}')

print('\n=== DONE ===')