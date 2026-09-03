from app import create_app, db
from app.models import Obito, Estabelecimento, CID

app = create_app()
with app.app_context():
    db.create_all()
    print('Tabelas criadas/verificadas!')
    
    # Verificar se as novas colunas existem
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    # Verificar colunas da tabela obitos
    cols = [c['name'] for c in inspector.get_columns('obitos')]
    print(f'Colunas em obitos: {cols}')
    
    if 'causas_morte_cids' not in cols:
        print('ERRO: coluna causas_morte_cids nao existe!')
    else:
        print('OK: coluna causas_morte_cids existe')
    
    if 'estabelecimento_id' not in cols:
        print('ERRO: coluna estabelecimento_id nao existe!')
    else:
        print('OK: coluna estabelecimento_id existe')
    
    # Verificar novas tabelas
    tables = inspector.get_table_names()
    print(f'Tabelas: {tables}')
    
    if 'estabelecimentos' in tables:
        print('OK: tabela estabelecimentos existe')
    else:
        print('ERRO: tabela estabelecimentos NAO existe')
    
    if 'cids' in tables:
        print('OK: tabela cids existe')
    else:
        print('ERRO: tabela cids NAO existe')