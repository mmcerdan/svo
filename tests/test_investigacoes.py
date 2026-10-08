import pytest
from datetime import date
from app.models import Investigacao, InvestigacaoCampo
from app.services.investigacao_service import InvestigacaoService
from app.utils.campos import get_campos_padrao_investigacao, get_tipo_campo, extrair_opcao
from app.utils.validators import ValidadorInvestigacao

# Obrigatórios do MIF para montar um form completo válido (como a tela real envia)
_OBRIGATORIOS_MIF = {
    'Nome da falecida': 'Teste',
    'Nº da DO': 'DO-001',
    'Data do óbito': '2024-01-01',
    'Zona: Urbana': 'X',
    'Grávida no momento do óbito? (Não sabe)': 'X',
}


def _montar_form_completo(investigacao, marcados=None):
    """Monta form com todos os campos da investigação + obrigatórios MIF preenchidos.

    marcados: dict {nome_campo: 'X'} para checkboxes adicionais.
    """
    form = {f'campo_{c.id}': c.valor for c in investigacao.campos}
    for c in investigacao.campos:
        if c.nome_campo in _OBRIGATORIOS_MIF:
            form[f'campo_{c.id}'] = _OBRIGATORIOS_MIF[c.nome_campo]
    if marcados:
        for nome, valor in marcados.items():
            for c in investigacao.campos:
                if c.nome_campo == nome:
                    form[f'campo_{c.id}'] = valor
    return form

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
        for tipo in ['MIF', 'MATERNO', 'INFANTIL_FETAL', 'MAL_DEFINIDA', 'INFANTIL', 'DENGUE']:
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
            'SEADE: S1': 'X',
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

    def test_dengue_sexo_obrigatorio(self):
        campos = {
            'DI03. Nome do paciente': 'Paciente Teste',
            'DI04. Data de nascimento': '1990-01-01',
        }
        erros = ValidadorInvestigacao.validar('DENGUE', campos)
        assert any('Sexo' in e for e in erros)

    def test_dengue_sexo_exato_um(self):
        # Sexo correto
        campos_ok = {
            'DI03. Nome do paciente': 'Paciente Teste',
            'DI04. Data de nascimento': '1990-01-01',
            'DI06. Sexo: Masculino': 'X',
            'DI06. Sexo: Feminino': '',
        }
        erros_ok = ValidadorInvestigacao.validar('DENGUE', campos_ok)
        assert len(erros_ok) == 0

        # Sexo duplo
        campos_duplo = {
            'DI03. Nome do paciente': 'Paciente Teste',
            'DI04. Data de nascimento': '1990-01-01',
            'DI06. Sexo: Masculino': 'X',
            'DI06. Sexo: Feminino': 'X',
        }
        erros_duplo = ValidadorInvestigacao.validar('DENGUE', campos_duplo)
        assert any('Sexo' in e for e in erros_duplo)

    def test_dengue_grupo_exclusivo_max_um(self):
        campos = {
            'DI03. Nome do paciente': 'Paciente',
            'DI04. Data de nascimento': '1990-01-01',
            'DI06. Sexo: Feminino': 'X',
            'IT05. Estadiamento: A': 'X',
            'IT05. Estadiamento: B': 'X',
        }
        erros = ValidadorInvestigacao.validar('DENGUE', campos)
        assert any('Estadiamento' in e for e in erros)

    def test_dengue_en_encerramento(self):
        # EN01 = Sim sem critério/classificação
        campos = {
            'DI03. Nome do paciente': 'Paciente',
            'DI04. Data de nascimento': '1990-01-01',
            'DI06. Sexo: Masculino': 'X',
            'EN01. Caso encerrado: Sim': 'X',
        }
        erros = ValidadorInvestigacao.validar('DENGUE', campos)
        assert any('EN02' in e for e in erros)
        assert any('EN03' in e for e in erros)

        # EN01 = Sim com critério e classificação
        campos_ok = dict(campos)
        campos_ok['EN02. Critério: Laboratorial'] = 'X'
        campos_ok['EN03. Classificação: 12 — Dengue grave'] = 'X'
        erros_ok = ValidadorInvestigacao.validar('DENGUE', campos_ok)
        assert len(erros_ok) == 0

class TestValidarConsistencia:
    """Testes da consistência ficha × óbito (alertas, nunca bloqueiam)."""

    @staticmethod
    def _obito_fake(**kwargs):
        from types import SimpleNamespace
        base = dict(numero_dob='DO-2024-0001', data_obito=date(2024, 1, 15),
                    nome='João da Silva')
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_do_divergente_gera_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nº da DO': 'DO-9999'}, self._obito_fake())
        assert len(alertas) == 1
        assert 'DO' in alertas[0]

    def test_do_igual_sem_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nº da DO': 'do-2024-0001'}, self._obito_fake())
        assert alertas == []

    def test_data_divergente_gera_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Data do óbito': '20/01/2024'}, self._obito_fake())
        assert len(alertas) == 1
        assert 'data' in alertas[0].lower()

    def test_data_igual_sem_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Data do óbito': '15/01/2024'}, self._obito_fake())
        assert alertas == []

    def test_nome_divergente_gera_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nome da falecida': 'Maria'}, self._obito_fake())
        assert len(alertas) == 1
        assert 'nome' in alertas[0].lower()

    def test_nome_com_espacos_diferentes_sem_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nome da falecida': '  João   da  Silva '}, self._obito_fake())
        assert alertas == []

    def test_todos_divergentes(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nº da DO': 'DO-X', 'Data do óbito': '01/02/2024',
                    'Nome do falecido': 'Outro'}, self._obito_fake())
        assert len(alertas) == 3

    def test_sem_obito_vinculado(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nº da DO': 'DO-X'}, None)
        assert alertas == []

    def test_campos_vazios_sem_alerta(self):
        alertas = ValidadorInvestigacao.validar_consistencia(
            'MIF', {'Nº da DO': '', 'Data do óbito': '',
                    'Nome da falecida': ''}, self._obito_fake())
        assert alertas == []


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
        
        # Checkbox livre (fora dos grupos exclusivos Zona/Grávida)
        checkbox = next(
            c for c in sample_investigacao.campos
            if get_tipo_campo(c.nome_campo) == 'checkbox'
            and c.nome_campo not in _OBRIGATORIOS_MIF
            and not c.nome_campo.startswith(('Zona:', 'Grávida'))
        )
        form_data = _montar_form_completo(sample_investigacao, {checkbox.nome_campo: 'X'})
        
        erros = InvestigacaoService.atualizar_campos(sample_investigacao, admin, form_data)
        assert len(erros) == 0
        assert checkbox.valor == 'X'

    def test_pendencias_ficha_vazia(self, db_session, sample_investigacao):
        validacao, alertas = InvestigacaoService.pendencias(sample_investigacao)
        assert len(validacao) > 0
        # campos vazios não geram divergência com o óbito
        assert alertas == []

    def test_pendencias_ficha_completa_divergente(self, db_session, sample_investigacao):
        for c in sample_investigacao.campos:
            if c.nome_campo in _OBRIGATORIOS_MIF:
                c.valor = _OBRIGATORIOS_MIF[c.nome_campo]
        db_session.session.commit()
        validacao, alertas = InvestigacaoService.pendencias(sample_investigacao)
        assert validacao == []
        assert any('DO' in a for a in alertas)
        assert any('data' in a.lower() for a in alertas)
        assert any('nome' in a.lower() for a in alertas)

    def test_finalizar_modo_aviso_ficha_vazia_finaliza(self, db_session, sample_investigacao, admin_user):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)

        erros = InvestigacaoService.finalizar(sample_investigacao, admin, 'Conclusão do caso.')
        assert erros == []
        assert sample_investigacao.status == 'CONCLUIDA'

    def test_finalizar_modo_bloqueio_ficha_vazia(self, db_session, sample_investigacao, admin_user, app):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        app.config['VALIDACAO_FICHA'] = 'bloqueio'
        try:
            erros = InvestigacaoService.finalizar(sample_investigacao, admin, 'Conclusão do caso.')
            assert len(erros) > 0
            assert sample_investigacao.status != 'CONCLUIDA'
        finally:
            app.config['VALIDACAO_FICHA'] = 'aviso'

    def test_finalizar_modo_bloqueio_ficha_completa(self, db_session, sample_investigacao, admin_user, app):
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        for c in sample_investigacao.campos:
            if c.nome_campo in _OBRIGATORIOS_MIF:
                c.valor = _OBRIGATORIOS_MIF[c.nome_campo]
        db_session.session.commit()
        app.config['VALIDACAO_FICHA'] = 'bloqueio'
        try:
            erros = InvestigacaoService.finalizar(sample_investigacao, admin, 'Conclusão do caso.')
            assert erros == []
            assert sample_investigacao.status == 'CONCLUIDA'
        finally:
            app.config['VALIDACAO_FICHA'] = 'aviso'

    def test_finalizar_modo_bloqueio_divergencia_nao_bloqueia(self, db_session, sample_investigacao, admin_user, app):
        # Divergências ficha × óbito são alertas: mesmo em modo bloqueio não impedem
        from app.models import Usuario
        admin = db_session.session.get(Usuario, admin_user.id)
        for c in sample_investigacao.campos:
            if c.nome_campo in _OBRIGATORIOS_MIF:
                c.valor = _OBRIGATORIOS_MIF[c.nome_campo]
        db_session.session.commit()
        app.config['VALIDACAO_FICHA'] = 'bloqueio'
        try:
            erros = InvestigacaoService.finalizar(sample_investigacao, admin, 'Conclusão do caso.')
            assert erros == []
            assert sample_investigacao.status == 'CONCLUIDA'
        finally:
            app.config['VALIDACAO_FICHA'] = 'aviso'

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
        # Envia o form completo como a tela real faz
        form_data = _montar_form_completo(sample_investigacao)
        response = auth_client.post(
            f'/investigacoes/{sample_investigacao.id}/salvar-campos-ajax',
            data=form_data,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        assert response.status_code == 200
        assert response.get_json()['sucesso'] is True
    
    def test_finalizar_via_post(self, auth_client, sample_investigacao):
        response = auth_client.post(
            f'/investigacoes/{sample_investigacao.id}/finalizar',
            data={'conclusao': 'Caso concluído via teste.'},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Conclu' in response.data

    def test_detalhe_mostra_pendencias(self, auth_client, sample_investigacao):
        response = auth_client.get(f'/investigacoes/{sample_investigacao.id}')
        assert response.status_code == 200
        assert 'Antes de finalizar' in response.data.decode('utf-8')

    def test_detalhe_sem_banner_apos_finalizar(self, auth_client, sample_investigacao):
        auth_client.post(
            f'/investigacoes/{sample_investigacao.id}/finalizar',
            data={'conclusao': 'Caso concluído.'},
            follow_redirects=True
        )
        response = auth_client.get(f'/investigacoes/{sample_investigacao.id}')
        assert 'Antes de finalizar' not in response.data.decode('utf-8')

    def test_finalizar_via_post_modo_bloqueio(self, auth_client, sample_investigacao, app):
        app.config['VALIDACAO_FICHA'] = 'bloqueio'
        try:
            response = auth_client.post(
                f'/investigacoes/{sample_investigacao.id}/finalizar',
                data={'conclusao': 'Caso concluído via teste.'},
                follow_redirects=True
            )
            assert response.status_code == 200
            texto = response.data.decode('utf-8')
            assert 'Campo obrigatório' in texto
            assert 'Antes de finalizar' in texto
        finally:
            app.config['VALIDACAO_FICHA'] = 'aviso'

    def test_nova_investigacao_mostra_avisos(self, auth_client, sample_obito):
        response = auth_client.post(
            f'/investigacoes/{sample_obito.id}/nova',
            data={'tipo': 'MIF', 'status': 'AGUARDANDO'},
            follow_redirects=True
        )
        assert response.status_code == 200
        texto = response.data.decode('utf-8')
        assert 'Investigação criada com sucesso' in texto
        assert 'Antes de finalizar' in texto