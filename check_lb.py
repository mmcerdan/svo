from app import create_app
from app.extensions import db
from app.models import Investigacao

app = create_app()
with app.app_context():
    invs = Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all()
    for inv in invs:
        campos_count = len(inv.campos.all())
        lb_count = len([c for c in inv.campos if 'Lista Brasileira' in c.nome_campo])
        print(f'Inv {inv.id}: {campos_count} campos, {lb_count} Lista Brasileira')