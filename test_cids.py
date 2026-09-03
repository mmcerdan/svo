from app import create_app
from app.models import CID, Estabelecimento
app = create_app()
with app.app_context():
    cids = CID.query.filter(CID.codigo.like('P%')).limit(5).all()
    for c in cids:
        print(c.codigo + ': ' + c.descricao[:50])
    print('Total CIDs:', CID.query.count())
    print('Total Estabelecimentos:', Estabelecimento.query.count())