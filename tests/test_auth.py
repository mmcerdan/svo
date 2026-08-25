import pytest
from app.models import Usuario

class TestAuth:
    """Testes de autenticacao."""
    
    def test_login_sucesso(self, client, admin_user):
        response = client.post('/auth/login', data={
            'usuario': 'admin_test',
            'senha': 'senha123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'Bem-vindo' in response.data.decode('utf-8')
    
    def test_login_falha_senha_errada(self, client, admin_user):
        response = client.post('/auth/login', data={
            'usuario': 'admin_test',
            'senha': 'senha_errada'
        })
        
        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'inv' in data or 'erro' in data
    
    def test_login_usuario_inexistente(self, client):
        response = client.post('/auth/login', data={
            'usuario': 'naoexiste',
            'senha': 'qualquer'
        })
        
        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'inv' in data or 'erro' in data
    
    def test_logout(self, auth_client):
        response = auth_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'Sess' in response.data.decode('utf-8')
    
    def test_acesso_sem_login(self, client):
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'login' in data

class TestUsuarioModel:
    """Testes do modelo Usuario."""
    
    def test_set_senha_valida(self, db_session):
        user = Usuario(nome='Teste', usuario='teste_senha', cargo='Usuario')
        user.set_senha('senha123')
        assert user.check_senha('senha123')
        assert not user.check_senha('errada')
    
    def test_set_senha_curta_falha(self, db_session):
        user = Usuario(nome='Teste', usuario='teste_curta', cargo='Usuario')
        with pytest.raises(ValueError):
            user.set_senha('123')
    
    def test_usuario_unico(self, db_session, admin_user):
        user = Usuario(nome='Outro', usuario='admin_test', cargo='Usuario')
        user.set_senha('senha123')
        db_session.session.add(user)
        with pytest.raises(Exception):
            db_session.session.commit()
