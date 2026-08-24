import sys
sys.path.insert(0, 'D:/Obito/SistemaObito')
from app import app, db, Obito
with app.app_context():
    o = db.session.get(Obito, 6)
    if o:
        inv = o.investigacoes.first()
        print(f'Obito 6: {o.nome}')
        print(f'Investigacao ID {inv.id}: tipo={inv.tipo}, status={inv.status}')
