#!/bin/bash
cd /opt/sistema-obito

sudo -u obito FLASK_ENV=production /opt/sistema-obito/venv/bin/python << 'PYEOF'
from app import create_app
from app.extensions import db
from app.models import Obito, Investigacao, InvestigacaoCampo, Usuario
from app.utils.campos import get_campos_padrao_investigacao
from datetime import date, datetime

app = create_app('production')
with app.app_context():
    user = Usuario.query.filter_by(usuario='admin').first()
    
    # Create test obito
    obito = Obito(
        nome='Maria da Silva Santos',
        data_nascimento=date(1985, 3, 15),
        data_obito=date(2026, 8, 20),
        sexo='F',
        nome_mae='Ana Maria da Silva',
        nome_pai='Joao Santos',
        numero_dob='DO-2026-001234',
        causa_morte='Hemorragia obstetrica',
        causa_morte_cid='O72',
        local_obito='HOSPITAL',
        municipio_ocorrencia='Goianira',
        endereco='Rua das Flores, 123 - Centro',
        observacoes='Caso de investigacao de obito materno',
        usuario_id=user.id,
    )
    db.session.add(obito)
    db.session.flush()
    
    # Create investigation MIF
    inv = Investigacao(
        obito_id=obito.id,
        tipo='MIF',
        status='EM_ANDAMENTO',
        responsavel='Dr. Carlos Lima',
        data_abertura=date(2026, 8, 21),
        usuario_id=user.id,
    )
    db.session.add(inv)
    db.session.flush()
    
    # Create fields
    campos_padrao = get_campos_padrao_investigacao('MIF')
    mapa = {
        'Nome da falecida': 'Maria da Silva Santos',
        'Nº da DO': 'DO-2026-001234',
        'Data do óbito': '20/08/2026',
        'Endereço': 'Rua das Flores, 123',
        'Número': '123',
        'Bairro': 'Centro',
        'Município de residência': 'Goianira',
        'UF residência': 'GO',
        'Zona: Urbana': 'X',
        'Zona: Rural': '',
        'Cartão SUS': '898 1234 5678 9012',
        'Município ocorrência': 'Goianira',
        'Grávida no momento do óbito? (Sim)': 'X',
        'Grávida no momento do óbito? (Não)': '',
        'Grávida no momento do óbito? (Não sabe)': '',
        'Esteve grávida nos 12 meses? (Sim)': 'X',
        'Esteve grávida nos 12 meses? (Não)': '',
        'Esteve grávida nos 12 meses? (Não sabe)': '',
        'Resumo do caso / justificativa': 'Paciente de 41 anos, gestante de 32 semanas, apresentou hemorragia grave. Foi encaminhada para hospital de referencia mas nao sobreviveu.',
        'Data da investigação': '25/08/2026',
        'Responsável investigação - nome': 'Dr. Carlos Lima',
    }
    for nome_campo in campos_padrao:
        campo = InvestigacaoCampo(
            investigacao_id=inv.id,
            nome_campo=nome_campo,
            valor=mapa.get(nome_campo, '')
        )
        db.session.add(campo)
    
    db.session.commit()
    print(f'Created obito #{obito.id} and investigation #{inv.id}')
    
    # Test PDF
    from app.utils.pdf import gerar_pdf_investigacao
    inv = db.session.get(Investigacao, inv.id)
    pdf_bytes = gerar_pdf_investigacao(inv)
    
    output_path = f'/tmp/test_investigacao_{inv.id}.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    print(f'PDF generated: {len(pdf_bytes)} bytes -> {output_path}')
PYEOF
