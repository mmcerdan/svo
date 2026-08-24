import pytest
from datetime import date
from app.models import Investigacao, InvestigacaoCampo
from app.services.investigacao_service import InvestigacaoService
from app.utils.campos import get_campos_padrao_investigacao, get_tipo_campo, extrair_opcao
from app.utils.validators import ValidadorInvestigacao

class TestCamposUtils:
    """Testes dos utilitários de campos."""
    
    def test_tipo_campo_checkbox_sim_nao(self):
        assert get_tipo_campo('Grávida no momento do óbito? (Sim)') == 'checkbox'
        assert get_tipo_campo('Grávida no momento do óbito? (Não)') == 'checkbox'
        assert get_tipo_campo('Grávida no momento do óbito? (Não sabe)') == 'checkbox'
    
    def test_tipo_campo_checkbox_dois_pontos(self):
        assert get_tipo_campo('Zona: Urbana') == 'checkbox'
        assert get_tipo_campo('Sexo: Masculino') == 'checkbox'
        assert get_tipo_campo('Wigglesworth: W1') == 'checkbox'
    
    def test_tipo_campo_textarea(self):
        assert get_tipo_campo('Nome da falecida') == 'textarea'
        assert get_tipo_campo('Endereço') == 'textarea'
        assert get_tipo_campo('Observações gerais') == 'textarea'
    
    def test_extrair_opcao(self):
        assert extrair_opcao('Zona: Urbana') == 'Urbana'
        assert extrair_opcao('Grávida? (Sim)') == 'Sim'
        assert extrair_opcao('Sexo: Feminino') == 'Feminino'
        assert extrair_opcao('Wigglesworth: W7') == 'W7'
    
    def test_campos_padrao_todos_tipos(self):
        for tipo in ['MIF', 'MATERNO', 'INFANTIL_FETAL', 'MAL_DEFINIDA', 'INFANTIL']:
            campos = get_campos_padrao_investigacao(tipo)
            assert len(campos) > 0
            # Verifica se tem checkboxes
            checkboxes = [c for c in campos if get_tipo_campo(c) == 'checkbox']
            assert len(checkboxes) > 0, f'{tipo} deve ter checkboxes'

class TestValidadorInvestigacao:
    """Testes do validador de investigação."""
    
    def test_mif_campos_obrigatorios(self):
        # MIF precisa de zona e grávida
        campos = {
            'Nome da falecida': 'Teste',
            'Nº da DO': 'DO-001',
            'Data do óbito': '2024-01-01',
            'Zona: Urbana': 'X',
            'Zona: Rural': '',
            'Grávida no momento do óbito? (Sim)': 'X',
            'Grávida no momento do óbito? (Não)': '',
            'Grávida no momento do óbito? (Não sabe)': '',
        }
        erros = ValidadorInvestigacao.validar('MIF', campos)
        assert len(erros) == 0
    
    def test_mif_falta_zona(self):
        campos = {
            'Nome da falecida': 'Teste',
            'Grávida no momento do óbito? (Sim)': 'X',
        }
        erros = ValidadorInvestigacao.validar('MIF', campos)
        assert any('Zona' in e for e in erros)
    
    def test_infantil_fetal_wigglesworth_exato_um(self):
        campos = {
            'Nome da criança': 'Bebê',
            'Nome da mãe': 'Mãe',
            'Nº do caso': '1',
            'Data de nascimento': '2024-01-01',
            'Nº da DN': 'DN-001',
            'Nº da DO': 'DO-001',
            'Data do óbito': '2024-01-01',
            'Peso ao nascer (gramas)': '3000',
            'Sexo: Masculino': 'X',
            'Wigglesworth: W1': 'X',
            'Wigglesworth: W2': '',
        }
        erros = ValidadorInvestigacao.validar('INFANTIL_FETAL', campos)
        assert len(erros) == 0
    
    def test_infantil_fetal_wigglesworth_zero_ou_multiplos(self):
        # Zero Wigglesworth
        campos = {
            'Nome da criança': 'Bebê',
            'Wigglesworth: W1': '',
            'Wigglesworth: W2': '',
        }
        erros = ValidadorInvestigacao.validar('INFANTIL_FETAL', campos)
        assert any('Wigglesworth' in e for e in erros)
        
        # Múltiplos Wigglesworth
        campos2 = {
            'Nome da criança': 'Bebê',
            'Wigglesworth: W1': 'X',
            'Wigglesworth: W2': 'X',
        }
        erros2 = ValidadorInvestigacao.validar('INFANTIL_FETAL', campos2)
        assert any('Wigglesworth' in e for e in erros2)
    
    def test_infantil_fetal_seade_pelo_menos_um(self):
        campos = {
            'Nome da criança': 'Bebê',
            'Wigglesworth: W1': 'X',
        }
        erros = ValidadorInvestigacao.validar('INFANTIL_FETAL', campos)
        assert any('SEADE' in e for e in erros)

class TestInvestigacaoService:
    """Testes do InvestigacaoService."""
    
    def test_criar_investigacao_com_campos(self, db_session, sample_obito, admin_user):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        
        inv, erros = InvestigacaoService.criar(admin, sample_obito, 'MIF')
        
        assert len(erros) == 0
        assert inv is not None
        assert inv.tipo == 'MIF'
        assert inv.status == 'AGUARDANDO'
        # Verifica se campos foram criados
        assert inv.campos.count() > 0
    
    def test_finalizar_investigacao_sem_conclusao(self, db_session, sample_investigacao, admin_user):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        
        erros = InvestigacaoService.finalizar(sample_investigacao, admin, '')
        assert len(erros) > 0
        assert 'obrigatória' in erros[0]
    
    def test_finalizar_investigacao_com_conclusao(self, db_session, sample_investigacao, admin_user):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        
        erros = InvestigacaoService.finalizar(sample_investigacao, admin, 'Conclusão do caso.')
        assert len(erros) == 0
        assert sample_investigacao.status == 'CONCLUIDA'
        assert sample_investigacao.data_conclusao is not None
        assert sample_investigacao.conclusao == 'Conclusão do caso.'
    
    def test_atualizar_campos_checkbox(self, db_session, sample_investigacao, admin_user):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        
        # Simula formulário com checkboxes
        form_data = {
            'campo_1': 'X',  # Assumindo primeiro campo
        }
        
        erros = InvestigacaoService.atualizar_campos(sample_investigacao, admin, form_data)
        assert len(erros) == 0

class TestInvestigacaoViews:
    """Testes das views de investigação (integration)."""
    
    def test_lista_investigacoes(self, auth_client, sample_investigacao):
        response = auth_client.get('/investigacoes/')
        assert response.status_code == 200
    
    def test_detalhe_investigacao(self, auth_client, sample_investigacao):
        response = auth_client.get(f'/investigacoes/{sample_investigacao.id}')
        assert response.status_code == 200
        assert b'MIF' in response.data or b'Mulher' in response.data
    
    def test_salvar_campos_ajax(self, auth_client, sample_investigacao):
        # Pega primeiro campo checkbox
        campo = sample_investigacao.campos.first()
        if campo:
            response = auth_client.post(
                f'/investigacoes/{sample_investigacao.id}/salvar-campos-ajax',
                data={f'campo_{campo.id}': 'X'},
                headers={'X-Requested-With': 'XMLHttpRequest'}
            )
            assert response.status_code == 200
    
    def test_finalizar_via_post(self, auth_client, sample_investigacao):
        response = auth_client.post(
            f'/investigacoes/{sample_investigacao.id}/finalizar',
            data={'conclusao': 'Caso concluído via teste.'},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Conclu' in response.data