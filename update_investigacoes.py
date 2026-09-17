from app import create_app
from app.extensions import db
from app.models import Investigacao, InvestigacaoCampo
from app.utils.campos import get_campos_padrao_investigacao

app = create_app()
with app.app_context():
    # Para cada investigação INFANTIL_FETAL, adicionar campos faltando
    invs = Investigacao.query.filter_by(tipo='INFANTIL_FETAL').all()
    campos_padrao = get_campos_padrao_investigacao('INFANTIL_FETAL')
    
    for inv in invs:
        existing = {c.nome_campo for c in inv.campos}
        missing = [c for c in campos_padrao if c not in existing]
        
        if missing:
            print(f'Investigação {inv.id}: adicionando {len(missing)} campos faltando')
            for nome in missing:
                campo = InvestigacaoCampo(investigacao_id=inv.id, nome_campo=nome, valor='')
                db.session.add(campo)
        else:
            print(f'Investigação {inv.id}: OK ({len(existing)} campos)')
    
    db.session.commit()
    print('\nAtualização concluída!')