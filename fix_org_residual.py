from app import create_app
from app.extensions import db
from app.models import Investigacao, InvestigacaoCampo

app = create_app()

# Campos residuais a remover (títulos de grupo sem sufixo Sim/Não/SR)
RESIDUAL_NAMES = [
    'Organizacao - Central regulacao',
    'Organizacao - Leitos UTI neonatal',
]

app = create_app()
with app.app_context():
    print("Removendo campos residuais...")
    
    invs = Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all()
    for inv in invs:
        for campo in inv.campos:
            if campo.nome_campo in RESIDUAL_NAMES:
                print(f'  Inv {inv.id}: REMOVENDO {campo.nome_campo}')
                db.session.delete(campo)
    
    db.session.commit()
    print("✓ Concluído!")

    # Verifica
    for inv in Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all():
        orgs = [c.nome_campo for c in inv.campos if c.nome_campo.startswith('Organizacao')]
        print(f'Inv {inv.id}: {len(orgs)} Org - {sorted(orgs)}')