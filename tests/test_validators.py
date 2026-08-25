import pytest
from datetime import date, timedelta
from app.utils.validators import (
    validar_cid10, 
    validar_data_obito, 
    validar_numero_dob, 
    ValidadorInvestigacao
)
from app.utils.security import sanitize_input, sanitize_html, validate_file_upload
from flask import Flask

class TestCID10:
    """Testes de validação CID-10."""
    
    codigos_validos = [
        'A00', 'A00.0', 'A00.9', 'A01', 'A01.0',
        'I21', 'I21.0', 'I21.9', 'I21.90',
        'Z00', 'Z00.0', 'Z00.00',
        'X00', 'X00.0', 'X99', 'Y00',
    ]
    
    codigos_invalidos = [
        '123', 'ABC', 'I2', 'I21.', 'I21.9.1',
        'I21.9.1.1', '1A1', 'AA1', 'I21.9.1.1.1',
    ]
    
    @pytest.mark.parametrize('cid', codigos_validos)
    def test_validos(self, cid):
        assert validar_cid10(cid) is True, f'{cid} deveria ser válido'
    
    @pytest.mark.parametrize('cid', codigos_invalidos)
    def test_invalidos(self, cid):
        assert validar_cid10(cid) is False, f'{cid} deveria ser inválido'

class TestDataObito:
    def test_data_valida(self):
        ok, msg = validar_data_obito(date(2024, 6, 15), date(1950, 1, 1))
        assert ok is True
    
    def test_data_futura(self):
        amanha = date.today() + timedelta(days=1)
        ok, msg = validar_data_obito(amanha)
        assert ok is False
        assert 'futura' in msg
    
    def test_data_antes_nascimento(self):
        ok, msg = validar_data_obito(date(2000, 1, 1), date(2010, 1, 1))
        assert ok is False
        assert 'anterior' in msg
    
    def test_idade_maxima_130_anos(self):
        ok, msg = validar_data_obito(date(2024, 1, 1), date(1850, 1, 1))
        assert ok is False
        assert '130' in msg

class TestSanitizeInput:
    def test_remove_script(self):
        entrada = '<script>alert(1)</script>Texto normal'
        resultado = sanitize_input(entrada)
        assert '<script>' not in resultado
        assert 'Texto normal' in resultado
    
    def test_remove_on_event(self):
        entrada = '<img src=x onerror=alert(1)>'
        resultado = sanitize_input(entrada)
        assert 'onerror' not in resultado
    
    def test_remove_javascript_protocol(self):
        entrada = '<a href="javascript:alert(1)">Link</a>'
        resultado = sanitize_input(entrada)
        assert 'javascript:' not in resultado.lower()
    
    def test_limite_tamanho(self):
        entrada = 'x' * 10000
        resultado = sanitize_input(entrada, max_length=100)
        assert len(resultado) == 100

class TestSanitizeHtml:
    def test_escapa_html(self):
        entrada = '<b>Negrito</b> & "aspas"'
        resultado = sanitize_html(entrada)
        assert '&lt;b&gt;' in resultado
        assert '&lt;/b&gt;' in resultado
        assert '&amp;' in resultado
        assert '&quot;' in resultado

class TestValidateFileUpload:
    def setup_method(self):
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = '/tmp'
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        self.ctx = self.app.test_request_context()
        self.ctx.push()
    
    def teardown_method(self):
        self.ctx.pop()
    
    def test_arquivo_vazio(self):
        class MockFile:
            filename = ''
        ok, msg = validate_file_upload(MockFile())
        assert ok is False
        assert 'Nenhum arquivo' in msg
    
    def test_extensao_invalida(self):
        class MockFile:
            filename = 'teste.exe'
        ok, msg = validate_file_upload(MockFile(), allowed_extensions={'pdf', 'jpg'})
        assert ok is False
        assert 'não permitida' in msg
    
    def test_extensao_valida(self):
        class MockFile:
            filename = 'documento.pdf'
        ok, msg = validate_file_upload(MockFile(), allowed_extensions={'pdf', 'jpg'})
        assert ok is True

class TestValidadorInvestigacao:
    """Testes consolidados do validador de investigação."""
    
    def test_mif_completo_valido(self):
        campos = {
            'Nome da falecida': 'Teste',
            'Nº da DO': 'DO-001',
            'Data do óbito': '2024-01-01',
            'Zona: Urbana': 'X',
            'Zona: Rural': '',
            'Grávida no momento do óbito? (Sim)': 'X',
            'Grávida no momento do óbito? (Não)': '',
            'Grávida no momento do óbito? (Não sabe)': '',
            'Esteve grávida nos 12 meses? (Sim)': 'X',
            'Esteve grávida nos 12 meses? (Não)': '',
            'Esteve grávida nos 12 meses? (Não sabe)': '',
        }
        erros = ValidadorInvestigacao.validar('MIF', campos)
        assert len(erros) == 0
    
    def test_infantil_fetal_wigglesworth_seade(self):
        # Wigglesworth: exatamente 1
        # SEADE: pelo menos 1
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
            'Sexo: Feminino': '',
            'Sexo: Ignorado': '',
            'Wigglesworth: W1': 'X',
            'Wigglesworth: W2': '',
            'Wigglesworth: W3': '',
            'Wigglesworth: W4': '',
            'Wigglesworth: W5': '',
            'Wigglesworth: W6': '',
            'Wigglesworth: W7': '',
            'Wigglesworth: W8': '',
            'Wigglesworth: W9': '',
            'SEADE: S1': 'X',
            'SEADE: S2': '',
        }
        erros = ValidadorInvestigacao.validar('INFANTIL_FETAL', campos)
        assert len(erros) == 0