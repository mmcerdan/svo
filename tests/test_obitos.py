import pytest
from datetime import date
from app.models import Obito
from app.services.obito_service import ObitoService
from app.utils.validators import validar_cid10, validar_data_obito, validar_numero_dob

class TestObitoValidators:
    """Testes dos validadores de obito."""
    
    def test_cid10_valido(self):
        assert validar_cid10('I21.9') is True
        assert validar_cid10('A00') is True
        assert validar_cid10('Z99.9') is True
        assert validar_cid10('') is True
    
    def test_cid10_invalido(self):
        assert validar_cid10('123') is False
        assert validar_cid10('II21.9') is False
        assert validar_cid10('I21.') is False
        assert validar_cid10('XYZ') is False
    
    def test_data_obito_valida(self):
        ok, msg = validar_data_obito(date(2024, 1, 15), date(1950, 1, 1))
        assert ok is True
        assert msg == ''
    
    def test_data_obito_futura(self):
        from datetime import date, timedelta
        amanha = date.today() + timedelta(days=1)
        ok, msg = validar_data_obito(amanha)
        assert ok is False
        assert 'futura' in msg
    
    def test_data_obito_antes_nascimento(self):
        ok, msg = validar_data_obito(date(2000, 1, 1), date(2010, 1, 1))
        assert ok is False
        assert 'anterior' in msg
    
    def test_numero_dob_gemeos_permitido(self, db_session, sample_obito):
        # v1.1: óbitos de gêmeos compartilham a mesma DO — nunca bloqueia
        ok, msg = validar_numero_dob('DO-2024-0001', sample_obito.id)
        assert ok is True

        ok, msg = validar_numero_dob('DO-2024-0001')
        assert ok is True

class TestObitoService:
    """Testes do ObitoService."""
    
    def test_criar_obito_valido(self, db_session, admin_user):
        dados = {
            'nome': 'Joao Teste',
            'data_nascimento': date(1950, 1, 1),
            'data_obito': date(2024, 1, 15),
            'sexo': 'M',
            'nome_mae': 'Maria',
            'numero_dob': 'DO-2024-0002',
            'causa_morte': 'Infarto',
            'causa_morte_cid': 'I21.9',
            'local_obito': 'HOSPITAL',
        }
        
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        obito, erros = ObitoService.criar(admin, dados)
        
        assert len(erros) == 0
        assert obito is not None
        assert obito.nome == 'Joao Teste'
        assert obito.numero_dob == 'DO-2024-0002'
    
    def test_criar_obito_cid_invalido(self, db_session, admin_user):
        dados = {
            'nome': 'Joao Teste',
            'data_nascimento': date(1950, 1, 1),
            'data_obito': date(2024, 1, 15),
            'numero_dob': 'DO-2024-0003',
            'causa_morte_cid': 'INVALIDO',
        }
        
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        obito, erros = ObitoService.criar(admin, dados)
        
        assert len(erros) > 0
        assert any('CID' in e for e in erros)
        assert obito is None
    
    def test_criar_obito_dob_duplicada_permitida(self, db_session, admin_user, sample_obito):
        # v1.1: DO duplicada aceita (gêmeos)
        dados = {
            'nome': 'Outro',
            'data_obito': date(2024, 1, 15),
            'numero_dob': sample_obito.numero_dob,
        }
        
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        obito, erros = ObitoService.criar(admin, dados)
        
        assert len(erros) == 0
        assert obito is not None
        assert obito.numero_dob == sample_obito.numero_dob

class TestAvisosCausasCids:
    """Avisos de CID-10 inválido na lista de causas (não bloqueia)."""

    def test_cids_invalidos_geram_aviso(self):
        dados = {'causas_morte_cids': [
            {'codigo': 'XYZ', 'descricao': ''},
            {'codigo': 'I21.9', 'descricao': ''},
            {'codigo': '1234', 'descricao': ''},
        ]}
        avisos = ObitoService.avisos_causas_cids(dados)
        assert len(avisos) == 2
        assert any('XYZ' in a for a in avisos)
        assert any('1234' in a for a in avisos)

    def test_cids_validos_sem_aviso(self):
        dados = {'causas_morte_cids': [
            {'codigo': 'I21.9', 'descricao': ''},
            {'codigo': 'a00', 'descricao': ''},
        ]}
        assert ObitoService.avisos_causas_cids(dados) == []

    def test_lista_vazia_sem_aviso(self):
        assert ObitoService.avisos_causas_cids({}) == []
        assert ObitoService.avisos_causas_cids({'causas_morte_cids': []}) == []

    def test_criar_obito_com_cid_lista_invalida_nao_bloqueia(self, db_session, admin_user):
        dados = {
            'nome': 'Teste Lista CID',
            'data_obito': date(2024, 1, 15),
            'numero_dob': 'DO-2024-0077',
            'causas_morte_cids': [{'codigo': 'ABC123', 'descricao': ''}],
        }
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        obito, erros = ObitoService.criar(admin, dados)
        assert erros == []
        assert obito is not None

class TestObitoViews:
    """Testes das views de obito (integration)."""
    
    def test_lista_obitos(self, auth_client, sample_obito):
        response = auth_client.get('/obitos/')
        assert response.status_code == 200
        assert 'Joao da Silva' in response.data.decode('utf-8') or 'Silva' in response.data.decode('utf-8')
    
    def test_novo_obito_get(self, auth_client):
        response = auth_client.get('/obitos/novo')
        assert response.status_code == 200
        assert 'bito' in response.data.decode('utf-8')
    
    def test_criar_obito_com_investigacao(self, auth_client):
        response = auth_client.post('/obitos/novo', data={
            'nome': 'Teste Integracao',
            'data_nascimento': '1950-01-01',
            'data_obito': '2024-01-20',
            'sexo': 'M',
            'nome_mae': 'Mae Teste',
            'numero_dob': 'DO-2024-0099',
            'causa_morte': 'Causa teste',
            'causa_morte_cid': 'I21.9',
            'local_obito': 'HOSPITAL',
            'criar_investigacao': 'MIF',
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'Investiga' in response.data.decode('utf-8')

    def test_editar_obito_avisa_cid_lista_invalida(self, auth_client, sample_obito):
        response = auth_client.post(f'/obitos/{sample_obito.id}/editar', data={
            'nome': 'João da Silva',
            'data_nascimento': '1950-01-01',
            'data_obito': '2024-01-15',
            'sexo': 'M',
            'numero_dob': 'DO-2024-0001',
            'causa_morte_cid': 'I21.9',
            'local_obito': 'HOSPITAL',
            'causas_morte_cids-0-codigo': 'XYZ99',
            'causas_morte_cids-0-descricao': 'Teste',
        }, follow_redirects=True)
        assert response.status_code == 200
        texto = response.data.decode('utf-8')
        assert 'Óbito atualizado com sucesso' in texto
        assert 'CID-10 inválido' in texto
