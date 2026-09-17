from app import create_app
from app.extensions import db
from app.models import Investigacao, InvestigacaoCampo

app = create_app()

# Mapeamento: nome antigo -> nome novo
LB_RENAME = {
    'Lista Brasileira 1.2: Sim': 'Lista Brasileira 1.2.1: Sim',
    'Lista Brasileira 1.2: Não': 'Lista Brasileira 1.2.1: Não',
    'Lista Brasileira 2.1: Sim': 'Lista Brasileira 1.2.2: Sim',
    'Lista Brasileira 2.1: Não': 'Lista Brasileira 1.2.2: Não',
    'Lista Brasileira 2.2: Sim': 'Lista Brasileira 1.2.3: Sim',
    'Lista Brasileira 2.2: Não': 'Lista Brasileira 1.2.3: Não',
    'Lista Brasileira 2.3: Sim': 'Lista Brasileira 2: Sim',
    'Lista Brasileira 2.3: Não': 'Lista Brasileira 2: Não',
    'Lista Brasileira 3.1: Sim': 'Lista Brasileira 3: Sim',
    'Lista Brasileira 3.1: Não': 'Lista Brasileira 3: Não',
    'Lista Brasileira 3.2: Sim': '',  # não existe na nova estrutura
    'Lista Brasileira 3.2: Não': '',
    'Lista Brasileira 3.3: Sim': '',  # não existe na nova estrutura
    'Lista Brasileira 3.3: Não': '',
}

app = create_app()
with app.app_context():
    print("Corrigindo nomes da Lista Brasileira...")
    
    invs = Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all()
    for inv in invs:
        for campo in inv.campos:
            if campo.nome_campo in LB_RENAME:
                novo = LB_RENAME[campo.nome_campo]
                if novo:
                    print(f'  Inv {inv.id}: {campo.nome_campo} -> {novo}')
                    campo.nome_campo = novo
                else:
                    print(f'  Inv {inv.id}: REMOVENDO {campo.nome_campo}')
                    db.session.delete(campo)
    
    db.session.commit()
    print("✓ Concluído!")

    # Verifica
    for inv in Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all():
        lbs = [c.nome_campo for c in inv.campos if 'Lista Brasileira' in c.nome_campo]
        print(f'Inv {inv.id}: {len(lbs)} LB - {sorted(lbs)}')