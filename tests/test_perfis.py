import pytest
from datetime import date


def _login(client, usuario, senha='senha123'):
    with client.session_transaction() as sess:
        sess['_fresh'] = True
    client.post('/auth/login', data={'usuario': usuario, 'senha': senha},
                follow_redirects=True)
    return client


@pytest.fixture
def supervisor_user(db_session):
    from app.models import Usuario
    u = Usuario(nome='Supervisor Test', usuario='sup_test', cargo='Supervisor', ativo=True)
    u.set_senha('senha123')
    db_session.session.add(u)
    db_session.session.commit()
    return u


@pytest.fixture
def supervisor_client(client, supervisor_user):
    return _login(client, 'sup_test')


@pytest.fixture
def investigador_user(db_session):
    from app.models import Usuario
    u = Usuario(nome='Investigador Test', usuario='inv_test', cargo='Investigador', ativo=True)
    u.set_senha('senha123')
    db_session.session.add(u)
    db_session.session.commit()
    return u


@pytest.fixture
def investigador_client(client, investigador_user):
    return _login(client, 'inv_test')


def _obito_de(usuario, db_session, numero_dob='DO-PRO-001'):
    from app.services.obito_service import ObitoService
    obito, erros = ObitoService.criar(usuario, {
        'nome': 'Registro do Dono',
        'data_obito': date(2024, 1, 10),
        'numero_dob': numero_dob,
    })
    assert erros == []
    db_session.session.commit()
    return obito


def _ficha_de(usuario, obito, db_session):
    from app.services.investigacao_service import InvestigacaoService
    inv, erros = InvestigacaoService.criar(usuario, obito, 'MIF')
    assert erros == []
    db_session.session.commit()
    return inv


class TestPerfisAdminSupervisor:
    """Admin = tudo; Supervisor = só operação (sem usuários/auditoria)."""

    def test_admin_acessa_usuarios(self, auth_client):
        assert auth_client.get('/admin/usuarios').status_code == 200

    def test_admin_acessa_auditoria(self, auth_client):
        assert auth_client.get('/admin/auditoria').status_code == 200

    def test_supervisor_sem_usuarios(self, supervisor_client):
        assert supervisor_client.get('/admin/usuarios').status_code == 403

    def test_supervisor_sem_auditoria(self, supervisor_client):
        assert supervisor_client.get('/admin/auditoria').status_code == 403

    def test_investigador_sem_usuarios(self, investigador_client):
        assert investigador_client.get('/admin/usuarios').status_code == 403

    def test_menu_admin_oculto_para_supervisor(self, supervisor_client):
        html = supervisor_client.get('/obitos/').data.decode('utf-8')
        assert 'Usuários' not in html
        assert 'Auditoria' not in html

    def test_menu_admin_visivel_para_admin(self, auth_client):
        html = auth_client.get('/obitos/').data.decode('utf-8')
        assert 'Usuários' in html
        assert 'Auditoria' in html


class TestPermissoesEdicao:
    """Regra de dono na edição: gestão edita tudo; operacionais, só o próprio."""

    def test_investigador_nao_edita_obito_de_outro(self, investigador_client, sample_obito):
        resp = investigador_client.post(f'/obitos/{sample_obito.id}/editar', data={
            'nome': 'Tentativa', 'data_obito': '2024-01-15',
        })
        assert resp.status_code == 403

    def test_supervisor_edita_obito_de_outro(self, supervisor_client, sample_obito):
        resp = supervisor_client.post(f'/obitos/{sample_obito.id}/editar', data={
            'nome': 'João da Silva',
            'data_nascimento': '1950-01-01',
            'data_obito': '2024-01-15',
            'sexo': 'M',
            'numero_dob': 'DO-2024-0001',
            'causa_morte_cid': 'I21.9',
            'local_obito': 'HOSPITAL',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert 'atualizado com sucesso' in resp.data.decode('utf-8')

    def test_investigador_edita_obito_proprio(self, investigador_client, investigador_user, db_session):
        obito = _obito_de(investigador_user, db_session)
        resp = investigador_client.post(f'/obitos/{obito.id}/editar', data={
            'nome': 'Registro do Dono Editado',
            'data_obito': '2024-01-10',
            'sexo': 'M',
            'numero_dob': 'DO-PRO-001',
            'local_obito': 'HOSPITAL',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert 'atualizado com sucesso' in resp.data.decode('utf-8')

    def test_investigador_nao_finaliza_ficha_de_outro(self, investigador_client, sample_investigacao):
        resp = investigador_client.post(
            f'/investigacoes/{sample_investigacao.id}/finalizar',
            data={'conclusao': 'Tentativa'})
        assert resp.status_code == 403
        assert sample_investigacao.status != 'CONCLUIDA'

    def test_supervisor_finaliza_ficha_de_outro(self, supervisor_client, sample_investigacao):
        resp = supervisor_client.post(
            f'/investigacoes/{sample_investigacao.id}/finalizar',
            data={'conclusao': 'Fechado pelo supervisor.'},
            follow_redirects=True)
        assert resp.status_code == 200
        assert sample_investigacao.status == 'CONCLUIDA'

    def test_salvar_campos_nao_dono_403(self, investigador_client, sample_investigacao):
        resp = investigador_client.post(
            f'/investigacoes/{sample_investigacao.id}/salvar-campos', data={})
        assert resp.status_code == 403

    def test_salvar_campos_dono_passa_permissao(self, investigador_client, investigador_user, db_session):
        obito = _obito_de(investigador_user, db_session, numero_dob='DO-PRO-002')
        inv = _ficha_de(investigador_user, obito, db_session)
        resp = investigador_client.post(f'/investigacoes/{inv.id}/salvar-campos', data={})
        # permissão liberada; falha apenas na validação de campos obrigatórios
        assert resp.status_code == 400

    def test_investigador_nao_anexa_em_ficha_de_outro(self, investigador_client, sample_investigacao):
        resp = investigador_client.post(
            f'/investigacoes/{sample_investigacao.id}/anexar')
        assert resp.status_code == 403


class TestPermissoesExclusao:
    """Exclusão restrita a Admin/Supervisor."""

    def test_investigador_nao_exclui_obito(self, investigador_client, sample_obito):
        from app.models import Obito
        resp = investigador_client.post(f'/obitos/{sample_obito.id}/excluir')
        assert resp.status_code == 403
        assert db_tem_obito(sample_obito.id)

    def test_usuario_comum_nao_exclui_obito(self, user_client, sample_obito):
        resp = user_client.post(f'/obitos/{sample_obito.id}/excluir')
        assert resp.status_code == 403
        assert db_tem_obito(sample_obito.id)

    def test_supervisor_exclui_obito(self, supervisor_client, sample_obito):
        resp = supervisor_client.post(f'/obitos/{sample_obito.id}/excluir',
                                      follow_redirects=True)
        assert resp.status_code == 200
        assert not db_tem_obito(sample_obito.id)

    def test_admin_exclui_obito(self, auth_client, sample_obito):
        resp = auth_client.post(f'/obitos/{sample_obito.id}/excluir',
                                follow_redirects=True)
        assert resp.status_code == 200
        assert not db_tem_obito(sample_obito.id)

    def test_investigador_nao_exclui_anexo(self, investigador_client, sample_investigacao, db_session):
        anexo = _criar_anexo(sample_investigacao, db_session)
        resp = investigador_client.post(f'/investigacoes/anexos/{anexo.id}/excluir')
        assert resp.status_code == 403
        from app.models import Anexo
        assert db_session.session.get(Anexo, anexo.id) is not None

    def test_supervisor_exclui_anexo(self, supervisor_client, sample_investigacao, db_session):
        anexo = _criar_anexo(sample_investigacao, db_session)
        resp = supervisor_client.post(f'/investigacoes/anexos/{anexo.id}/excluir',
                                      follow_redirects=True)
        assert resp.status_code == 200
        from app.models import Anexo
        assert db_session.session.get(Anexo, anexo.id) is None


def db_tem_obito(obito_id):
    from app.extensions import db
    from app.models import Obito
    return db.session.get(Obito, obito_id) is not None


def _criar_anexo(investigacao, db_session):
    from app.models import Anexo
    a = Anexo(
        investigacao_id=investigacao.id,
        nome_original='teste.pdf',
        nome_arquivo='teste.pdf',
        tipo='pdf',
        tamanho=10,
    )
    db_session.session.add(a)
    db_session.session.commit()
    return a
