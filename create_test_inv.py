from app import create_app
from app.models import Obito, Investigacao, Usuario
from datetime import date

app = create_app()
with app.app_context():
    # Verificar dados existentes
    print("Obits:", Obito.query.count())
    print("Invs:", Investigacao.query.count())
    
    # Criar óbito de teste se não existir
    user = Usuario.query.first()
    if not Obito.query.filter_by(numero_dob='TESTE-001').first():
        obito = Obito(
            nome='Teste Silva',
            data_nascimento=date(2020, 1, 15),
            data_obito=date(2026, 8, 20),
            sexo='M',
            nome_mae='Maria Silva',
            nome_pai='João Silva',
            numero_dob='TESTE-001',
            causa_morte='Sepse neonatal',
            causa_morte_cid='P369',
            causas_morte_cids=[{'codigo': 'P369', 'descricao': 'Sepse bacteriana do recém-nascido, não especificada'}],
            local_obito='HOSPITAL',
            municipio_ocorrencia='Goianira',
            endereco='Rua Teste, 123',
            observacoes='Óbito de teste para investigação',
            usuario_id=user.id,
        )
        from app.extensions import db
        db.session.add(obito)
        db.session.commit()
        print(f"Obito criado: {obito.id}")
    else:
        obito = Obito.query.filter_by(numero_dob='TESTE-001').first()
        print(f"Obito existente: {obito.id}")
    
    # Criar investigação se não existir
    if not Investigacao.query.filter_by(obito_id=obito.id, tipo='INFANTIL_FETAL').first():
        inv = Investigacao(
            obito_id=obito.id,
            tipo='INFANTIL_FETAL',
            status='EM_ANDAMENTO',
            responsavel=user.nome,
            data_abertura=date.today(),
            conclusao='Investigação de teste em andamento',
            observacoes='Criada via script',
            usuario_id=user.id,
        )
        db.session.add(inv)
        db.session.commit()
        print(f"Investigação criada: {inv.id}")
    else:
        inv = Investigacao.query.filter_by(obito_id=obito.id, tipo='INFANTIL_FETAL').first()
        print(f"Investigação existente: {inv.id}")
    
    print(f"\nAcesse: http://192.168.0.225:9010/investigacoes/{inv.id}")