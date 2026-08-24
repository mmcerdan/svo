import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Usuario, Obito, Investigacao
from datetime import date, datetime

@pytest.fixture(scope='session')
def app():
    """Cria app para testes."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['WTF_CSRF_ENABLED'] = 'False'
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Sessão de banco para testes."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.rollback()
        db.drop_all()

@pytest.fixture
def admin_user(db_session):
    """Cria usuário admin para testes."""
    user = Usuario(nome='Admin Test', usuario='admin_test', cargo='Admin', ativo=True)
    user.set_senha('senha123')
    db_session.session.add(user)
    db_session.session.commit()
    return user

@pytest.fixture
def regular_user(db_session):
    """Cria usuário comum para testes."""
    user = Usuario(nome='User Test', usuario='user_test', cargo='Usuário', ativo=True)
    user.set_senha('senha123')
    db_session.session.add(user)
    db_session.session.commit()
    return user

@pytest.fixture
def sample_obito(db_session, admin_user):
    """Cria óbito de exemplo."""
    obito = Obito(
        nome='João da Silva',
        data_nascimento=date(1950, 1, 1),
        data_obito=date(2024, 1, 15),
        sexo='M',
        nome_mae='Maria da Silva',
        numero_dob='DO-2024-0001',
        causa_morte='Infarto agudo do miocárdio',
        causa_morte_cid='I21.9',
        local_obito='HOSPITAL',
        municipio_ocorrencia='Goianira',
        endereco='Rua A, 123',
        usuario_id=admin_user.id,
    )
    db_session.session.add(obito)
    db_session.session.commit()
    return obito

@pytest.fixture
def sample_investigacao(db_session, sample_obito, admin_user):
    """Cria investigação de exemplo."""
    from app.services.investigacao_service import InvestigacaoService
    from app.utils.campos import get_campos_padrao_investigacao
    
    inv = Investigacao(
        obito_id=sample_obito.id,
        tipo='MIF',
        status='AGUARDANDO',
        data_abertura=date.today(),
        usuario_id=admin_user.id,
    )
    db_session.session.add(inv)
    db_session.session.flush()
    
    # Cria campos padrão
    for nome_campo in get_campos_padrao_investigacao('MIF'):
        campo = InvestigacaoCampo(investigacao_id=inv.id, nome_campo=nome_campo, valor='')
        db_session.session.add(campo)
    
    db_session.session.commit()
    return inv

@pytest.fixture
def auth_client(client, admin_user):
    """Cliente autenticado como admin."""
    client.post('/auth/login', data={
        'usuario': 'admin_test',
        'senha': 'senha123'
    }, follow_redirects=True)
    return client

@pytest.fixture
def user_client(client, regular_user):
    """Cliente autenticado como usuário comum."""
    client.post('/auth/login', data={
        'usuario': 'user_test',
        'senha': 'senha123'
    }, follow_redirects=True)
    return client