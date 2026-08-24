import pytest
from app.models import Usuario

class TestAuth:
    """Testes de autenticação."""
    
    def test_login_sucesso(self, client, admin_user):
        """Login com credenciais válidas."""
        response = client.post('/auth/login', data={
            'usuario': 'admin_test',
            'senha': 'senha123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Bem-vindo' in response.data
    
    def test_login_falha_senha_errada(self, client, admin_user):
        """Login com senha incorreta."""
        response = client.post('/auth/login', data={
            'usuario': 'admin_test',
            'senha': 'senha_errada'
        })
        
        assert response.status_code == 200
        assert b'inv' in response.data.lower() or b'erro' in response.data.lower()
    
    def test_login_usuario_inexistente(self, client):
        """Login com usuário que não existe."""
        response = client.post('/auth/login', data={
            'usuario': 'naoexiste',
            'senha': 'qualquer'
        })
        
        assert response.status_code == 200
        assert b'inv' in response.data.lower() or b'erro' in response.data.lower()
    
    def test_logout(self, auth_client):
        """Logout bem-sucedido."""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sessão encerrada' in response.data
    
    def test_acesso_sem_login(self, client):
        """Acesso a rota protegida sem login."""
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'Login' in response.data

class TestUsuarioModel:
    """Testes do modelo Usuario."""
    
    def test_set_senha_valida(self, db_session):
        user = Usuario(nome='Teste', usuario='teste_senha', cargo='Usuário')
        user.set_senha('senha123')
        assert user.check_senha('senha123')
        assert not user.check_senha('errada')
    
    def test_set_senha_curta_falha(self, db_session):
        user = Usuario(nome='Teste', usuario='teste_curta', cargo='Usuário')
        with pytest.raises(ValueError):
            user.set_senha('123')
    
    def test_usuario_unico(self, db_session, admin_user):
        user = Usuario(nome='Outro', usuario='admin_test', cargo='Usuário')
        user.set_senha('senha123')
        db_session.session.add(user)
        with pytest.raises(Exception):  # IntegrityError
            db_session.session.commit()