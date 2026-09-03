from app import create_app
from app.extensions import db
from app.models import Obito, Estabelecimento, CID

app = create_app()
with app.app_context():
    # Adicionar colunas faltantes na tabela obitos (SQLite)
    with db.engine.connect() as conn:
        # Verificar colunas existentes
        result = conn.execute(db.text("PRAGMA table_info(obitos)"))
        cols = [row[1] for row in result.fetchall()]
        print(f'Colunas atuais: {cols}')
        
        # Adicionar causas_morte_cids
        if 'causas_morte_cids' not in cols:
            conn.execute(db.text("ALTER TABLE obitos ADD COLUMN causas_morte_cids JSON DEFAULT '[]'"))
            print('Adicionada coluna causas_morte_cids')
        else:
            print('Coluna causas_morte_cids ja existe')
        
        # Adicionar estabelecimento_id
        if 'estabelecimento_id' not in cols:
            conn.execute(db.text("ALTER TABLE obitos ADD COLUMN estabelecimento_id INTEGER REFERENCES estabelecimentos(id)"))
            print('Adicionada coluna estabelecimento_id')
        else:
            print('Coluna estabelecimento_id ja existe')
        
        conn.commit()
    
    print('Migracao concluida!')