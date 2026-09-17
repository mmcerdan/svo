from app import create_app
from app.extensions import db
from app.models import Investigacao, InvestigacaoCampo

app = create_app()

# Nomes antigos de Organização para remover
OLD_ORG_NAMES = [
    'Organização - Cobertura atenção primária: Sim',
    'Organização - Cobertura atenção primária: Não',
    'Organização - Cobertura atenção primária: SR',
    'Organização - Referência/contrarreferência: Sim',
    'Organização - Referência/contrarreferência: Não',
    'Organização - Referência/contrarreferência: SR',
    'Organização - Pré-natal alto risco: Sim',
    'Organização - Pré-natal alto risco: Não',
    'Organização - Pré-natal alto risco: SR',
    'Organização - Leito UTI gestante: Sim',
    'Organização - Leito UTI gestante: Não',
    'Organização - Leito UTI gestante: SR',
    'Organização - Leitos UTI neonatal: Sim',
    'Organização - Leitos UTI neonatal: Não',
    'Organização - Leitos UTI neonatal: SR',
    'Organização - Central regulação: Sim',
    'Organização - Central regulação: Não',
    'Organização - Central regulação: SR',
    'Organização - Transporte pré/inter-hospitalar: Sim',
    'Organização - Transporte pré/inter-hospitalar: Não',
    'Organização - Transporte pré/inter-hospitalar: SR',
    'Organização - Bancos de sangue: Sim',
    'Organização - Bancos de sangue: Não',
    'Organização - Bancos de sangue: SR',
    'Organização - Outros: Sim',
    'Organização - Outros: Não',
    'Organização - Outros: SR',
]

app = create_app()
with app.app_context():
    print("Removendo nomes antigos de Organização...")
    
    invs = Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all()
    for inv in invs:
        for campo in inv.campos:
            if campo.nome_campo in OLD_ORG_NAMES:
                print(f'  Inv {inv.id}: REMOVENDO {campo.nome_campo}')
                db.session.delete(campo)
    
    db.session.commit()
    print("✓ Concluído!")

    # Verifica
    for inv in Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all():
        orgs = [c.nome_campo for c in inv.campos if c.nome_campo.startswith('Organizacao')]
        print(f'Inv {inv.id}: {len(orgs)} Org - {sorted(orgs)}')