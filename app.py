import os
import uuid
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, jsonify
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import (
    StringField, TextAreaField, DateField, SelectField,
    PasswordField, SubmitField, IntegerField
)
from wtforms.validators import DataRequired, Optional, Length

app = Flask(__name__)
app.config['SECRET_KEY'] = 'goianira-sim-obito-2026-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///obito.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar o sistema.'

@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now(), 'get_tipo_campo': get_tipo_campo, 'agrupar_campos': agrupar_campos}

TIPOS_INVESTIGACAO = [
    ('MIF', 'MIF - Mulher em Idade Fértil'),
    ('MATERNO', 'Materno'),
    ('INFANTIL_FETAL', 'Infantil/Fetal'),
    ('MAL_DEFINIDA', 'Causa Mal Definida'),
    ('INFANTIL', 'Infantil'),
]

STATUS_INVESTIGACAO = [
    ('AGUARDANDO', 'Aguardando'),
    ('EM_ANDAMENTO', 'Em Andamento'),
    ('CONCLUIDA', 'Concluída'),
    ('ARQUIVADA', 'Arquivada'),
]

LOCAIS_OBITO = [
    ('HOSPITAL', 'Hospital'),
    ('DOMICILIO', 'Domicílio'),
    ('VIA_PUBLICA', 'Via Pública'),
    ('OUTROS', 'Outros'),
]

# ===================== MODELS =====================

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(50), default='Usuário')
    ativo = db.Column(db.Boolean, default=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Obito(db.Model):
    __tablename__ = 'obitos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    data_nascimento = db.Column(db.Date)
    data_obito = db.Column(db.Date, nullable=False, index=True)
    sexo = db.Column(db.String(1))
    nome_mae = db.Column(db.String(200))
    nome_pai = db.Column(db.String(200))
    numero_dob = db.Column(db.String(50))
    causa_morte = db.Column(db.Text)
    causa_morte_cid = db.Column(db.String(10))
    local_obito = db.Column(db.String(50))
    municipio_ocorrencia = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.now)
    atualizado_em = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', backref='obitos')

    investigacoes = db.relationship('Investigacao', backref='obito', lazy='dynamic',
                                     cascade='all, delete-orphan')

    def idade_obito(self):
        if not self.data_nascimento or not self.data_obito:
            return None
        return self.data_obito.year - self.data_nascimento.year - (
            (self.data_obito.month, self.data_obito.day) <
            (self.data_nascimento.month, self.data_nascimento.day)
        )

    def ultima_investigacao(self):
        return self.investigacoes.order_by(Investigacao.criado_em.desc()).first()


class Investigacao(db.Model):
    __tablename__ = 'investigacoes'
    id = db.Column(db.Integer, primary_key=True)
    obito_id = db.Column(db.Integer, db.ForeignKey('obitos.id'), nullable=False)
    tipo = db.Column(db.String(30), nullable=False, index=True)
    status = db.Column(db.String(20), default='AGUARDANDO')
    responsavel = db.Column(db.String(100))
    data_abertura = db.Column(db.Date, default=date.today)
    data_conclusao = db.Column(db.Date)
    conclusao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.now)
    atualizado_em = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', backref='investigacoes')

    campos = db.relationship('InvestigacaoCampo', backref='investigacao', lazy='dynamic',
                              cascade='all, delete-orphan')
    anexos = db.relationship('Anexo', backref='investigacao', lazy='dynamic',
                              cascade='all, delete-orphan')

    def tipo_display(self):
        for k, v in TIPOS_INVESTIGACAO:
            if k == self.tipo:
                return v
        return self.tipo

    def status_display(self):
        for k, v in STATUS_INVESTIGACAO:
            if k == self.status:
                return v
        return self.status


class InvestigacaoCampo(db.Model):
    __tablename__ = 'investigacao_campos'
    id = db.Column(db.Integer, primary_key=True)
    investigacao_id = db.Column(db.Integer, db.ForeignKey('investigacoes.id'), nullable=False)
    nome_campo = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Text)


class Anexo(db.Model):
    __tablename__ = 'anexos'
    id = db.Column(db.Integer, primary_key=True)
    investigacao_id = db.Column(db.Integer, db.ForeignKey('investigacoes.id'), nullable=False)
    nome_original = db.Column(db.String(200))
    nome_arquivo = db.Column(db.String(200))
    tipo = db.Column(db.String(50))
    data_upload = db.Column(db.DateTime, default=datetime.now)

# ===================== FORMS =====================

class LoginForm(FlaskForm):
    usuario = StringField('Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])

class ObitoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    data_nascimento = DateField('Data de Nascimento', validators=[Optional()])
    data_obito = DateField('Data do Óbito', validators=[DataRequired()])
    sexo = SelectField('Sexo', choices=[('', 'Selecione...'), ('M', 'Masculino'), ('F', 'Feminino')],
                       validators=[Optional()])
    nome_mae = StringField('Nome da Mãe', validators=[Optional(), Length(max=200)])
    nome_pai = StringField('Nome do Pai', validators=[Optional(), Length(max=200)])
    numero_dob = StringField('Nº Declaração de Óbito', validators=[Optional(), Length(max=50)])
    causa_morte = TextAreaField('Causa da Morte', validators=[Optional()])
    causa_morte_cid = StringField('CID da Causa da Morte', validators=[Optional(), Length(max=10)])
    local_obito = SelectField('Local do Óbito', choices=[('', 'Selecione...')] + LOCAIS_OBITO,
                              validators=[Optional()])
    municipio_ocorrencia = StringField('Município da Ocorrência', validators=[Optional(), Length(max=100)])
    endereco = TextAreaField('Endereço', validators=[Optional()])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    criar_investigacao = SelectField('Criar Investigação', choices=[
        ('', 'Apenas cadastrar óbito'),
        ('MIF', 'MIF - Mulher em Idade Fértil'),
        ('MATERNO', 'Materno'),
        ('INFANTIL_FETAL', 'Infantil/Fetal'),
        ('MAL_DEFINIDA', 'Causa Mal Definida'),
        ('INFANTIL', 'Infantil'),
    ], validators=[Optional()])

class InvestigacaoForm(FlaskForm):
    tipo = SelectField('Tipo de Investigação', choices=TIPOS_INVESTIGACAO, validators=[DataRequired()])
    status = SelectField('Status', choices=STATUS_INVESTIGACAO, validators=[DataRequired()])
    responsavel = StringField('Responsável', validators=[Optional(), Length(max=100)])
    data_abertura = DateField('Data de Abertura', validators=[Optional()])
    data_conclusao = DateField('Data de Conclusão', validators=[Optional()])
    conclusao = TextAreaField('Conclusão', validators=[Optional()])
    observacoes = TextAreaField('Observações', validators=[Optional()])

# ===================== AUTH =====================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.cargo not in ('Admin', 'Supervisor'):
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(usuario=form.usuario.data).first()
        if user and user.check_senha(form.senha.data) and user.ativo:
            login_user(user)
            flash(f'Bem-vindo, {user.nome}!', 'success')
            return redirect(url_for('index'))
        flash('Usuário ou senha inválidos.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))

# ===================== ROTAS PRINCIPAIS =====================

@app.route('/')
@login_required
def index():
    total_obitos = Obito.query.count()
    total_investigacoes = Investigacao.query.count()
    pendentes = Investigacao.query.filter_by(status='AGUARDANDO').count()
    concluidas = Investigacao.query.filter_by(status='CONCLUIDA').count()
    ultimos_obitos = Obito.query.order_by(Obito.criado_em.desc()).limit(5).all()

    inv_tipos = []
    for k, v in TIPOS_INVESTIGACAO:
        count = Investigacao.query.filter_by(tipo=k).count()
        inv_tipos.append({'tipo': k, 'descricao': v, 'count': count})

    return render_template('index.html', total_obitos=total_obitos,
                           total_investigacoes=total_investigacoes,
                           pendentes=pendentes, concluidas=concluidas,
                           ultimos_obitos=ultimos_obitos, inv_tipos=inv_tipos)

# ===================== ROTAS ÓBITOS =====================

@app.route('/obitos')
@login_required
def lista_obitos():
    busca = request.args.get('busca', '')
    page = request.args.get('page', 1, type=int)

    query = Obito.query
    if busca:
        query = query.filter(
            db.or_(
                Obito.nome.ilike(f'%{busca}%'),
                Obito.numero_dob.ilike(f'%{busca}%'),
                Obito.nome_mae.ilike(f'%{busca}%'),
            )
        )
    query = query.order_by(Obito.data_obito.desc())
    obitos = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('obitos/lista.html', obitos=obitos, busca=busca)


@app.route('/obitos/novo', methods=['GET', 'POST'])
@login_required
def novo_obito():
    form = ObitoForm()
    if form.validate_on_submit():
        obito = Obito(
            nome=form.nome.data,
            data_nascimento=form.data_nascimento.data,
            data_obito=form.data_obito.data,
            sexo=form.sexo.data,
            nome_mae=form.nome_mae.data,
            nome_pai=form.nome_pai.data,
            numero_dob=form.numero_dob.data,
            causa_morte=form.causa_morte.data,
            causa_morte_cid=form.causa_morte_cid.data,
            local_obito=form.local_obito.data,
            municipio_ocorrencia=form.municipio_ocorrencia.data,
            endereco=form.endereco.data,
            observacoes=form.observacoes.data,
            usuario_id=current_user.id,
        )
        db.session.add(obito)
        db.session.commit()

        tipo_inv = form.criar_investigacao.data
        if tipo_inv:
            inv = Investigacao(
                obito_id=obito.id,
                tipo=tipo_inv,
                status='AGUARDANDO',
                data_abertura=date.today(),
                usuario_id=current_user.id,
            )
            db.session.add(inv)
            db.session.flush()

            campos_padrao = get_campos_padrao_investigacao(tipo_inv)
            for nome_campo in campos_padrao:
                # Pre-fill from form data where names match obito fields
                valor = request.form.get(f'inv_{nome_campo}', '')
                campo = InvestigacaoCampo(investigacao_id=inv.id, nome_campo=nome_campo, valor=valor)
                db.session.add(campo)
            db.session.commit()

            flash('Óbito cadastrado com investigação!', 'success')
            return redirect(url_for('detalhe_investigacao', id=inv.id))

        flash('Óbito cadastrado com sucesso!', 'success')
        return redirect(url_for('detalhe_obito', id=obito.id))
    return render_template('obitos/form.html', form=form, titulo='Novo Óbito')


@app.route('/obitos/<int:id>')
@login_required
def detalhe_obito(id):
    obito = db.session.get(Obito, id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('lista_obitos'))
    return render_template('obitos/detalhe.html', obito=obito)


@app.route('/obitos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_obito(id):
    obito = db.session.get(Obito, id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('lista_obitos'))
    form = ObitoForm(obj=obito)
    if form.validate_on_submit():
        form.populate_obj(obito)
        obito.atualizado_em = datetime.now()
        db.session.commit()
        flash('Óbito atualizado com sucesso!', 'success')
        return redirect(url_for('detalhe_obito', id=obito.id))
    return render_template('obitos/form.html', form=form, titulo='Editar Óbito', obito=obito)


@app.route('/obitos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_obito(id):
    obito = db.session.get(Obito, id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('lista_obitos'))
    db.session.delete(obito)
    db.session.commit()
    flash('Óbito excluído permanentemente.', 'success')
    return redirect(url_for('lista_obitos'))

# ===================== ROTAS INVESTIGAÇÕES =====================

@app.route('/investigacoes')
@login_required
def lista_investigacoes():
    tipo = request.args.get('tipo', '')
    status = request.args.get('status', '')
    busca = request.args.get('busca', '')
    page = request.args.get('page', 1, type=int)

    query = Investigacao.query
    if tipo:
        query = query.filter_by(tipo=tipo)
    if status:
        query = query.filter_by(status=status)
    if busca:
        query = query.join(Obito).filter(Obito.nome.ilike(f'%{busca}%'))
    query = query.order_by(Investigacao.criado_em.desc())
    investigacoes = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('investigacoes/lista.html', investigacoes=investigacoes,
                           tipo=tipo, status=status, busca=busca,
                           tipos_inv=TIPOS_INVESTIGACAO, status_inv=STATUS_INVESTIGACAO)


@app.route('/obitos/<int:obito_id>/investigacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_investigacao(obito_id):
    obito = db.session.get(Obito, obito_id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('lista_obitos'))
    form = InvestigacaoForm()
    if form.validate_on_submit():
        inv = Investigacao(
            obito_id=obito.id,
            tipo=form.tipo.data,
            status=form.status.data or 'AGUARDANDO',
            responsavel=form.responsavel.data,
            data_abertura=form.data_abertura.data or date.today(),
            data_conclusao=form.data_conclusao.data,
            conclusao=form.conclusao.data,
            observacoes=form.observacoes.data,
            usuario_id=current_user.id,
        )
        db.session.add(inv)
        db.session.commit()

        campos_padrao = get_campos_padrao_investigacao(form.tipo.data)
        for nome_campo in campos_padrao:
            campo = InvestigacaoCampo(investigacao_id=inv.id, nome_campo=nome_campo, valor='')
            db.session.add(campo)
        db.session.commit()

        flash('Investigação criada com sucesso!', 'success')
        return redirect(url_for('detalhe_investigacao', id=inv.id))
    return render_template('investigacoes/form.html', form=form, obito=obito, titulo='Nova Investigação')


@app.route('/investigacoes/campos-por-tipo/<tipo>')
@login_required
def campos_por_tipo(tipo):
    if tipo not in dict(TIPOS_INVESTIGACAO):
        return jsonify({'erro': 'Tipo inválido'}), 400
    campos = get_campos_padrao_investigacao(tipo)
    # Build list of dicts with tipo info
    items = []
    for nome in campos:
        items.append({
            'nome': nome,
            'tipo': get_tipo_campo(nome),
            'grupo': get_grupo_campo(nome),
        })
    grupos = agrupar_campos_list(items)
    return jsonify({'campos': items, 'grupos': grupos})


def agrupar_campos_list(items):
    """Agrupa items (dicts com 'nome') consecutivos pelo mesmo grupo."""
    if not items:
        return []
    grupos = []
    grupo_atual = None
    for item in items:
        if item['tipo'] == 'checkbox':
            grp = item['grupo']
            if grupo_atual and grupo_atual['titulo'] == grp:
                grupo_atual['campos'].append(item)
            else:
                grupo_atual = {'tipo': 'grupo', 'titulo': grp, 'campos': [item]}
                grupos.append(grupo_atual)
        else:
            grupo_atual = None
            grupos.append({'tipo': 'campo', 'campo': item})
    return grupos


@app.route('/investigacoes/<int:id>')
@login_required
def detalhe_investigacao(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('lista_investigacoes'))
    return render_template('investigacoes/detalhe.html', inv=inv)


@app.route('/investigacoes/<int:id>/imprimir')
@login_required
def imprimir_investigacao(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('lista_investigacoes'))
    campos_dict = {c.nome_campo: c.valor for c in inv.campos}

    # Mapear campos antigos (combinados) para novos (individuais)
    obito = inv.obito
    if inv.tipo == 'INFANTIL':
        mapeamentos = {
            'Nome da criança / Nome da mãe': ('Nome da crianca', None),
            'Nº da DO / Nº da DN': ('N\u00ba da DO', 'N\u00ba da DN'),
            'Peso ao nascer (gramas)': ('Peso ao nascer (gramas)', None),
            'Idade ao óbito (meses/dias/horas)': ('Idade ao obito', None),
            'Nº do Cartão SUS / Equipe PSF': ('N\u00ba do Cartao SUS', 'Equipe/PACS/PSF'),
            'Pré-natal: número de consultas': ('N\u00ba de consultas pre-natal', None),
            'Patologias na gestação': ('Patologias/fatores de risco', None),
            'Aleitamento materno exclusivo?': ('Aleitamento materno exclusivo?', None),
            'Vacinação completa para idade?': ('Vacinacao completa?', None),
            'Causa do óbito registrada no prontuário': ('Causa do obito no prontuario', None),
            'Resumo do caso / conclusão': ('O que aconteceu (investigador)', None),
        }
        for campo_antigo, (campo_novo1, campo_novo2) in mapeamentos.items():
            if campo_antigo in campos_dict and campo_novo1 not in campos_dict:
                valor = campos_dict[campo_antigo]
                if campo_novo1 and campo_novo2 and ' / ' in valor:
                    partes = valor.split(' / ', 1)
                    campos_dict[campo_novo1] = partes[0].strip()
                    campos_dict[campo_novo2] = partes[1].strip() if len(partes) > 1 else ''
                elif campo_novo1:
                    campos_dict[campo_novo1] = valor
            if campo_novo2 and campo_novo2 not in campos_dict:
                campos_dict[campo_novo2] = ''

    if inv.tipo == 'MAL_DEFINIDA':
        mapeamentos = {
            'Nº da DO / Causa básica original': ('N\u00ba da DO', 'Causa basica original'),
            'Nome da Unidade Básica de Saúde': ('Nome da Unidade Basica/USF', None),
            'Patologias que motivavam atendimentos': ('Patologias/motivos de atendimento', None),
            'Data e motivo da última consulta': ('Data da ultima consulta', 'Motivo da ultima consulta'),
            'Estabelecimento de saúde da internação': ('Nome do estabelecimento de saude', None),
            'Data da internação / alta': ('Data da internacao', 'Data da alta'),
            'Hipótese diagnóstica da alta': ('Hipotese diagnostica da alta', None),
            'Resultados de exames relevantes': ('Resultados de exames relevantes', None),
            'Causa do óbito no prontuário': ('Causa do obito no prontuario', None),
            'Investigação em outros locais (SINAN/IML/SVO)': ('Investigacao SINAN', None),
            'Causas da morte após investigação / CID': ('Causa basica - diagnostico', None),
        }
        for campo_antigo, (campo_novo1, campo_novo2) in mapeamentos.items():
            if campo_antigo in campos_dict and campo_novo1 not in campos_dict:
                valor = campos_dict[campo_antigo]
                if campo_novo1 and campo_novo2 and ' / ' in valor:
                    partes = valor.split(' / ', 1)
                    campos_dict[campo_novo1] = partes[0].strip()
                    campos_dict[campo_novo2] = partes[1].strip() if len(partes) > 1 else ''
                elif campo_novo1:
                    campos_dict[campo_novo1] = valor
            if campo_novo2 and campo_novo2 not in campos_dict:
                campos_dict[campo_novo2] = ''

    if inv.tipo == 'MIF':
        mapeamentos = {
            'Estava grávida no momento do óbito?': ('Gr\u00e1vida no momento do \u00f3bito? (Sim)', None),
            'Esteve grávida nos 12 meses anteriores?': ('Esteve gr\u00e1vida nos 12 meses? (Sim)', None),
            'Urbano/Rural': ('Zona: Urbana', 'Zona: Rural'),
            'Resumo do caso / justificativa': ('Resumo do caso / justificativa', None),
        }
        for campo_antigo, (campo_novo1, campo_novo2) in mapeamentos.items():
            if campo_antigo in campos_dict and campo_novo1 not in campos_dict:
                valor = campos_dict[campo_antigo]
                if campo_novo1 and campo_novo2 and ' / ' in valor:
                    partes = valor.split(' / ', 1)
                    campos_dict[campo_novo1] = partes[0].strip()
                    campos_dict[campo_novo2] = partes[1].strip() if len(partes) > 1 else ''
                elif 'Urbano/Rural' == campo_antigo:
                    v = valor.lower()
                    campos_dict['Zona: Urbana'] = 'X' if 'urbano' in v else ''
                    campos_dict['Zona: Rural'] = 'X' if 'rural' in v else ''
                elif campo_novo1:
                    campos_dict[campo_novo1] = valor
            if campo_novo2 and campo_novo2 not in campos_dict:
                campos_dict[campo_novo2] = ''

    if inv.tipo == 'MATERNO':
        mapeamentos = {
            'Nº da DO / Data do óbito': ('N\u00ba da DO', 'Data do \u00f3bito'),
            'Idade gestacional na 1ª consulta': ('IG 1\u00aa consulta (semanas)', None),
            'Número de consultas pré-natal': ('N\u00ba consultas pr\u00e9-natal', None),
            'Foi considerada gestante de alto risco?': ('Gestante alto risco? (Sim)', None),
            'Patologias/fatores de risco na gestação': ('Patologias/fatores de risco', None),
            'Foi internada durante a gestação? Motivo?': ('Internada na gesta\u00e7\u00e3o? (Sim)', 'Motivos da interna\u00e7\u00e3o'),
            'Causas do óbito registradas no prontuário': ('Causa do \u00f3bito no prontu\u00e1rio', None),
            'Resumo do caso / conclusão': ('O que aconteceu (investigador)', None),
        }
        for campo_antigo, (campo_novo1, campo_novo2) in mapeamentos.items():
            if campo_antigo not in campos_dict or not campo_novo1:
                continue
            if campo_novo1 in campos_dict:
                continue
            valor = campos_dict[campo_antigo]
            if campo_novo1 and campo_novo2 and ' / ' in valor:
                partes = valor.split(' / ', 1)
                campos_dict[campo_novo1] = partes[0].strip()
                campos_dict[campo_novo2] = partes[1].strip() if len(partes) > 1 else ''
            elif campo_novo1:
                campos_dict[campo_novo1] = valor
            if campo_novo2 and campo_novo2 not in campos_dict:
                campos_dict[campo_novo2] = ''

    if inv.tipo == 'INFANTIL_FETAL':
        mapeamentos = {
            'Nº da DO / Nº da DN': ('N\u00ba da DO', 'N\u00ba da DN'),
            'Idade gestacional (semanas)': ('Idade gestacional (semanas)', None),
            'Faixa etária (fetal/neonatal/pós-neonatal)': ('Faixa et\u00e1ria: Fetal', None),
            'Idade da mãe / Escolaridade materna': ('Idade da m\u00e3e (anos)', 'Escolaridade m\u00e3e - anos'),
            'Classificação de evitabilidade': ('Wigglesworth: W1', None),
            'Recomendações e medidas de prevenção': ('Recomenda\u00e7\u00f5es / propostas de interven\u00e7\u00e3o', None),
        }
        for campo_antigo, (campo_novo1, campo_novo2) in mapeamentos.items():
            if campo_antigo in campos_dict and campo_novo1 and campo_novo1 not in campos_dict:
                valor = campos_dict[campo_antigo]
                if campo_novo1 and campo_novo2 and ' / ' in valor:
                    partes = valor.split(' / ', 1)
                    campos_dict[campo_novo1] = partes[0].strip()
                    campos_dict[campo_novo2] = partes[1].strip() if len(partes) > 1 else ''
                elif 'Faixa et' in campo_antigo:
                    v = valor.lower()
                    for f in ['Fetal', 'Neonatal precoce', 'Neonatal tardio', 'Pós-neonatal', 'Ignorado']:
                        key = f'Faixa et\u00e1ria: {f}'
                        if f.lower() in v:
                            campos_dict[key] = 'X'
                elif campo_novo1:
                    campos_dict[campo_novo1] = valor
            if campo_novo2 and campo_novo2 not in campos_dict:
                campos_dict[campo_novo2] = ''

    tipo = inv.tipo
    template_map = {
        'MIF': 'investigacoes/imprimir_mif.html',
        'MATERNO': 'investigacoes/imprimir_materno.html',
        'INFANTIL_FETAL': 'investigacoes/imprimir_infantil_fetal.html',
        'MAL_DEFINIDA': 'investigacoes/imprimir_mal_definida.html',
        'INFANTIL': 'investigacoes/imprimir_infantil.html',
    }
    tmpl = template_map.get(tipo, 'investigacoes/imprimir.html')
    return render_template(tmpl, inv=inv, c=campos_dict, now=datetime.now())


@app.route('/investigacoes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_investigacao(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('lista_investigacoes'))
    form = InvestigacaoForm(obj=inv)
    if form.validate_on_submit():
        form.populate_obj(inv)
        inv.atualizado_em = datetime.now()
        db.session.commit()
        flash('Investigação atualizada!', 'success')
        return redirect(url_for('detalhe_investigacao', id=inv.id))
    return render_template('investigacoes/form.html', form=form, obito=inv.obito,
                           titulo='Editar Investigação', inv=inv)


@app.route('/investigacoes/<int:id>/finalizar', methods=['POST'])
@login_required
def finalizar_investigacao(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('lista_investigacoes'))
    inv.status = 'CONCLUIDA'
    inv.data_conclusao = date.today()
    inv.conclusao = request.form.get('conclusao', '')
    db.session.commit()
    flash('Investigação concluída com sucesso!', 'success')
    return redirect(url_for('detalhe_investigacao', id=inv.id))


@app.route('/investigacoes/<int:id>/salvar-campos', methods=['POST'])
@login_required
def salvar_campos_investigacao(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        return jsonify({'erro': 'Investigação não encontrada'}), 404
    for campo in inv.campos:
        if get_tipo_campo(campo.nome_campo) == 'checkbox':
            campo.valor = 'X' if request.form.get(f'campo_{campo.id}') else ''
        else:
            campo.valor = request.form.get(f'campo_{campo.id}', '')
    db.session.commit()
    flash('Campos da investigação salvos!', 'success')
    return redirect(url_for('detalhe_investigacao', id=inv.id))


@app.route('/investigacoes/<int:id>/anexar', methods=['POST'])
@login_required
def anexar_arquivo(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('lista_investigacoes'))
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('detalhe_investigacao', id=inv.id))
    arquivo = request.files['arquivo']
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('detalhe_investigacao', id=inv.id))
    ext = arquivo.filename.rsplit('.', 1)[-1].lower() if '.' in arquivo.filename else ''
    nome_arquivo = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo))
    anexo = Anexo(
        investigacao_id=inv.id,
        nome_original=secure_filename(arquivo.filename) or arquivo.filename,
        nome_arquivo=nome_arquivo,
        tipo=ext,
    )
    db.session.add(anexo)
    db.session.commit()
    flash('Arquivo anexado com sucesso!', 'success')
    return redirect(url_for('detalhe_investigacao', id=inv.id))


@app.route('/uploads/<nome_arquivo>')
@login_required
def download_anexo(nome_arquivo):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nome_arquivo)


@app.route('/anexos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_anexo(id):
    anexo = db.session.get(Anexo, id)
    if not anexo:
        flash('Anexo não encontrado.', 'danger')
        return redirect(url_for('lista_investigacoes'))
    inv_id = anexo.investigacao_id
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], anexo.nome_arquivo)
    if os.path.exists(caminho):
        os.remove(caminho)
    db.session.delete(anexo)
    db.session.commit()
    flash('Anexo excluído.', 'success')
    return redirect(url_for('detalhe_investigacao', id=inv_id))

# ===================== ROTAS RELATÓRIOS =====================

@app.route('/relatorios')
@login_required
def relatorios():
    return render_template('relatorios/index.html')


@app.route('/relatorios/dados')
@login_required
def relatorios_dados():
    tipo = request.args.get('tipo', 'geral')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')

    query_obitos = Obito.query
    query_inv = Investigacao.query

    if data_inicio:
        di = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        query_obitos = query_obitos.filter(Obito.data_obito >= di)
        query_inv = query_inv.join(Obito).filter(Obito.data_obito >= di)
    if data_fim:
        df = datetime.strptime(data_fim, '%Y-%m-%d').date()
        query_obitos = query_obitos.filter(Obito.data_obito <= df)
        query_inv = query_inv.join(Obito).filter(Obito.data_obito <= df)

    if tipo == 'geral':
        total = query_obitos.count()
        por_sexo = db.session.query(Obito.sexo, db.func.count(Obito.id)).group_by(Obito.sexo).all()
        por_local = db.session.query(Obito.local_obito, db.func.count(Obito.id)).group_by(Obito.local_obito).all()
        return jsonify({
            'total': total,
            'por_sexo': [{'label': s or 'Não informado', 'value': c} for s, c in por_sexo],
            'por_local': [{'label': l or 'Não informado', 'value': c} for l, c in por_local],
        })
    elif tipo == 'investigacoes':
        total = query_inv.count()
        por_tipo = db.session.query(Investigacao.tipo, db.func.count(Investigacao.id))
        if data_inicio or data_fim:
            por_tipo = por_tipo.join(Obito)
            if data_inicio:
                por_tipo = por_tipo.filter(Obito.data_obito >= di)
            if data_fim:
                por_tipo = por_tipo.filter(Obito.data_obito <= df)
        por_tipo = por_tipo.group_by(Investigacao.tipo).all()
        por_status = db.session.query(Investigacao.status, db.func.count(Investigacao.id))
        if data_inicio or data_fim:
            por_status = por_status.join(Obito)
            if data_inicio:
                por_status = por_status.filter(Obito.data_obito >= di)
            if data_fim:
                por_status = por_status.filter(Obito.data_obito <= df)
        por_status = por_status.group_by(Investigacao.status).all()
        tipo_map = dict(TIPOS_INVESTIGACAO)
        status_map = dict(STATUS_INVESTIGACAO)
        return jsonify({
            'total': total,
            'por_tipo': [{'label': tipo_map.get(t, t), 'value': c} for t, c in por_tipo],
            'por_status': [{'label': status_map.get(s, s), 'value': c} for s, c in por_status],
        })
    elif tipo == 'causas':
        causas = query_obitos.with_entities(Obito.causa_morte_cid, db.func.count(Obito.id))
        causas = causas.filter(Obito.causa_morte_cid.isnot(None))
        causas = causas.group_by(Obito.causa_morte_cid).order_by(db.func.count(Obito.id).desc()).limit(15).all()
        return jsonify({
            'causas': [{'label': c or 'Sem CID', 'value': v} for c, v in causas],
        })
    return jsonify({'erro': 'Tipo inválido'}), 400


# ===================== ROTAS ADMIN =====================

@app.route('/admin/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin_usuarios.html', usuarios=usuarios)


@app.route('/admin/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        cargo = request.form.get('cargo', 'Usuário')
        if not nome or not usuario or not senha:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return render_template('admin_usuario_form.html')
        if Usuario.query.filter_by(usuario=usuario).first():
            flash('Nome de usuário já existe.', 'danger')
            return render_template('admin_usuario_form.html')
        u = Usuario(nome=nome, usuario=usuario, cargo=cargo)
        u.set_senha(senha)
        db.session.add(u)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('lista_usuarios'))
    return render_template('admin_usuario_form.html')


@app.route('/admin/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    u = db.session.get(Usuario, id)
    if not u:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('lista_usuarios'))
    if request.method == 'POST':
        u.nome = request.form.get('nome')
        u.cargo = request.form.get('cargo', 'Usuário')
        senha = request.form.get('senha')
        if senha:
            u.set_senha(senha)
        db.session.commit()
        flash('Usuário atualizado!', 'success')
        return redirect(url_for('lista_usuarios'))
    return render_template('admin_usuario_form.html', usuario=u)


@app.route('/admin/usuarios/<int:id>/ativar', methods=['POST'])
@login_required
@admin_required
def ativar_usuario(id):
    u = db.session.get(Usuario, id)
    if u:
        u.ativo = not u.ativo
        db.session.commit()
    return redirect(url_for('lista_usuarios'))

# ===================== CAMPOS PADRÃO =====================

def get_campos_padrao_investigacao(tipo):
    campos = {
        'MIF': [
            'Nome da falecida',
            'Nº da DO',
            'Data do óbito',
            'Endereço',
            'Número',
            'Complemento',
            'Bairro',
            'Distrito/Povoado',
            'Zona: Urbana',
            'Zona: Rural',
            'Município de residência',
            'UF residência',
            'Cartão SUS',
            'Equipe/PACS/PSF',
            'Centro Saúde/UBS',
            'Distrito Sanitário',
            'Local de ocorrência',
            'Nome estabelecimento',
            'Código CNES',
            'Município ocorrência',
            'UF ocorrência',
            'Grávida no momento do óbito? (Sim)',
            'Grávida no momento do óbito? (Não)',
            'Grávida no momento do óbito? (Não sabe)',
            'Esteve grávida nos 12 meses? (Sim)',
            'Esteve grávida nos 12 meses? (Não)',
            'Esteve grávida nos 12 meses? (Não sabe)',
            'Resumo do caso / justificativa',
            'Data da investigação',
            'Responsável investigação - nome',
            'Responsável investigação - carimbo/rubrica',
        ],
        'MATERNO': [
            'Nome da falecida',
            'Nº da DO',
            'Data do óbito',
            'Endereço',
            'Número',
            'Complemento',
            'Bairro',
            'Distrito/Povoado',
            'Zona: Urbana',
            'Zona: Rural',
            'Tipo seguro saúde',
            'Centro de Saúde/UBS',
            'Equipe/PACS/PSF - nome',
            'Sem cobertura ESF',
            'Distrito Sanitário',
            'Nome serviço pré-natal',
            'Código CNES (pré-natal)',
            'Tipo serviço: CS SUS',
            'Tipo serviço: Convênio',
            'Tipo serviço: Particular',
            'Não fez pré-natal',
            'IG 1ª consulta (semanas)',
            'IG 1ª consulta (meses)',
            'IG 1ª consulta SR',
            'IG última consulta (semanas)',
            'IG última consulta (meses)',
            'IG última consulta SR',
            'Nº consultas pré-natal',
            'Nº consultas SR',
            'Cadastrada no Sisprenatal? (Sim)',
            'Cadastrada no Sisprenatal? (Não)',
            'Cadastrada no Sisprenatal? (SR)',
            'Já esteve grávida antes? (Sim)',
            'Já esteve grávida antes? (Não)',
            'Já esteve grávida antes? (SR)',
            'Nº gestações',
            'Nº partos',
            'Nº abortos',
            'Histórico gestações SR',
            'Partos normais',
            'Partos fórceps',
            'Partos cesáreos',
            'Tipos parto SR',
            'Gestante alto risco? (Sim)',
            'Gestante alto risco? (Não)',
            'Gestante alto risco? (SR)',
            'Acompanhada PNAR? (Sim/Qual)',
            'Acompanhada PNAR? (Não)',
            'Acompanhada PNAR? (SR)',
            'A partir de semanas (PNAR)',
            'Acompanhamento AB mantido? (Sim)',
            'Acompanhamento AB mantido? (Não)',
            'Acompanhamento AB mantido? (SR)',
            'Internada na gestação? (Sim)',
            'Internada na gestação? (Não)',
            'Internada na gestação? (SR)',
            'Quantas internações?',
            'Motivos da internação',
            '1ª internação (semanas)',
            '1ª internação (local)',
            '2ª internação (semanas)',
            '2ª internação (local)',
            'Patologias/fatores de risco',
            'Uso de medicação? (Sim)',
            'Uso de medicação? (Não)',
            'Uso de medicação? (SR)',
            'Quais medicamentos?',
            'Vacinação tétano: 1ª dose',
            'Vacinação tétano: 2ª dose',
            'Vacinação tétano: 3ª dose',
            'Vacinação tétano: Reforço',
            'Vacinação tétano: Imune',
            'Vacinação tétano: SR',
            'Visita domiciliar pré-natal? (Sim)',
            'Visita domiciliar pré-natal? (Não)',
            'Visita domiciliar pré-natal? (SR)',
            'Motivo da visita domiciliar',
            'Observações do pré-natal',
            'Resp. investigação PN - nome',
            'Resp. investigação PN - profissão',
            'Causa do óbito no prontuário',
            'Observações gerais',
            'O que aconteceu (investigador)',
            'Data de encerramento',
            'Resp. investigação geral - nome',
            'Resp. investigação geral - carimbo',
        ],
        'INFANTIL_FETAL': [
            'Nome da criança',
            'Nome da mãe',
            'Nº do caso',
            'Data de nascimento',
            'Nº da DN',
            'Nº da DO',
            'Data do óbito',
            'Tipo óbito fetal: Anteparto',
            'Tipo óbito fetal: Intraparto',
            'Peso ao nascer (gramas)',
            'Sexo: Masculino',
            'Sexo: Feminino',
            'Sexo: Ignorado',
            'Idade ao óbito',
            'Idade gestacional (semanas)',
            'Idade gestacional (meses)',
            'IG ignorado',
            'Faixa etária: Fetal',
            'Faixa etária: Neonatal precoce',
            'Faixa etária: Neonatal tardio',
            'Faixa etária: Pós-neonatal',
            'Faixa etária: Ignorado',
            'Idade da mãe (anos)',
            'Escolaridade mãe - anos',
            'Escolaridade mãe - série',
            'Escolaridade mãe - grau',
            'Escolaridade mãe - ignorado',
            'Município residência',
            'UF residência',
            'Município ocorrência',
            'UF ocorrência',
            'Resumo do caso',
            'Fonte: Prontuários ambulatoriais',
            'Fonte: Entrevista domiciliar',
            'Fonte: Autópsia verbal',
            'Fonte: Registros urgência/emergência',
            'Fonte: Registros hospitalares',
            'Fonte: SVO',
            'Fonte: IML',
            'Estabelecimentos saúde pré-natal',
            'Avaliação - Assistência pré-natal',
            'Avaliação - Assistência ao parto',
            'Avaliação - Assistência RN sala parto',
            'Avaliação - Assistência RN alojamento',
            'Avaliação - Assistência RN UTI neonatal',
            'Avaliação - Assistência criança atenção básica',
            'Avaliação - Assistência criança urgência',
            'Avaliação - Assistência criança hospital',
            'Avaliação - Dificuldades da família',
            'Avaliação - Causas externas',
            'Organização - Cobertura atenção primária',
            'Organização - Referência/contrarreferência',
            'Organização - Pré-natal alto risco',
            'Organização - Leito UTI gestante',
            'Organização - Leitos UTI neonatal',
            'Organização - Central regulação',
            'Organização - Transporte pré/inter-hospitalar',
            'Organização - Bancos de sangue',
            'Organização - Outros',
            'Óbito evitável? (Sim)',
            'Óbito evitável? (Não)',
            'Óbito evitável? (Inconclusivo)',
            'Wigglesworth: W1',
            'Wigglesworth: W2',
            'Wigglesworth: W3',
            'Wigglesworth: W4',
            'Wigglesworth: W5',
            'Wigglesworth: W6',
            'Wigglesworth: W7',
            'Wigglesworth: W8',
            'Wigglesworth: W9',
            'SEADE: S1',
            'SEADE: S2',
            'SEADE: S3',
            'SEADE: S4',
            'SEADE: S5',
            'SEADE: S6',
            'SEADE: S7',
            'Fatores determinantes / comentários',
            'Recomendações / propostas de intervenção',
            'Data da conclusão',
            'Comitê: Municipal',
            'Comitê: Hospitalar',
            'Comitê: Regional',
            'Comitê: Estadual',
            'Responsável preenchimento - nome',
            'Responsável preenchimento - carimbo/rubrica',
        ],
        'MAL_DEFINIDA': [
            'Nº da DO',
            'Nome do falecido',
            'Nome da mãe',
            'Data de nascimento',
            'Data do óbito',
            'Causa básica original',
            'Nome da Unidade Básica/USF',
            'Nº prontuário UBS',
            'Tempo de moradia no domicílio',
            'Cadastrado na USF',
            'Patologias/motivos de atendimento',
            'Data da última consulta',
            'Motivo da última consulta',
            'Nome do estabelecimento de saúde',
            'Nº prontuário hospitalar',
            'Data da internação',
            'Data da alta',
            'Estado do paciente na hospitalização',
            'Motivo da alta',
            'Atendimento pré-hospitalar',
            'Hipótese diagnóstica da alta',
            'Resultados de exames relevantes',
            'Procedimentos realizados',
            'Causa do óbito no prontuário',
            'Investigação SINAN',
            'Investigação IML',
            'Investigação SVO',
            'Investigação FUNASA',
            'Investigação jornal/internet',
            'Formulário utilizado (autópsia verbal)',
            'Causa direta - diagnóstico',
            'Causa direta - CID',
            'Antecedente (linha b) - diagnóstico',
            'Antecedente (linha b) - CID',
            'Antecedente (linha c) - diagnóstico',
            'Antecedente (linha c) - CID',
            'Causa básica - diagnóstico',
            'Causa básica - CID',
            'Outras condições significativas',
            'Data da conclusão',
            'Responsável pela investigação',
            'Coordenador Vigilância SIM',
        ],
        'INFANTIL': [
            'Nome da criança',
            'Nome da mãe',
            'Nº da DO',
            'Data do óbito',
            'Nº da DN',
            'Data de nascimento',
            'Sexo',
            'Sexo: Masculino',
            'Sexo: Feminino',
            'Sexo: Ignorado',
            'Peso ao nascer (gramas)',
            'Idade ao óbito',
            'Idade óbito - meses',
            'Idade óbito - dias',
            'Idade óbito - horas',
            'Idade óbito - minutos',
            'Idade óbito ignorado',
            'Nº do Cartão SUS',
            'Equipe/PACS/PSF',
            'Centro de Saúde/UBS',
            'Distrito Sanitário',
            'Nome do serviço de pré-natal',
            'Código CNES',
            'Tipo de serviço',
            'Tipo serviço: CS SUS',
            'Tipo serviço: Convênio',
            'Tipo serviço: Particular',
            'Não fez pré-natal',
            'IG na 1ª consulta (semanas)',
            'IG na 1ª consulta (meses)',
            'IG 1ª consulta sem registro',
            'Nº de consultas pré-natal',
            'Nº consultas sem registro',
            'Esteve grávida antes? (Sim)',
            'Esteve grávida antes? (Não)',
            'Esteve grávida antes? (SR)',
            'Nº gestações',
            'Nº partos',
            'Nº abortos',
            'Histórico gestações SR',
            'Partos normais',
            'Partos fórceps',
            'Partos cesáreos',
            'Tipos parto SR',
            'Gestante de alto risco? (Sim)',
            'Gestante de alto risco? (Não)',
            'Gestante de alto risco? (SR)',
            'Detalhe do alto risco',
            'Acompanhada PNAR? (Sim/Qual)',
            'Acompanhada PNAR? (Não)',
            'Acompanhada PNAR? (SR)',
            'A partir de quantas semanas?',
            'Acompanhamento AB mantido? (Sim)',
            'Acompanhamento AB mantido? (Não)',
            'Acompanhamento AB mantido? (SR)',
            'Internada durante a gestação? (Sim)',
            'Internada durante a gestação? (Não)',
            'Internada durante a gestação? (SR)',
            'Quantas internações?',
            'Motivos da internação',
            '1ª internação - semanas',
            '1ª internação - local',
            '2ª internação - semanas',
            '2ª internação - local',
            'Patologias/fatores de risco',
            'Uso de medicação na gestação? (Sim)',
            'Uso de medicação na gestação? (Não)',
            'Uso de medicação na gestação? (SR)',
            'Quais medicamentos?',
            'Esquema vacinação tétano: 1ª dose',
            'Esquema vacinação tétano: 2ª dose',
            'Esquema vacinação tétano: 3ª dose',
            'Esquema vacinação tétano: Reforço',
            'Esquema vacinação tétano: Imune',
            'Esquema vacinação tétano: SR',
            'Visita domiciliar pré-natal? (Sim)',
            'Visita domiciliar pré-natal? (Não)',
            'Visita domiciliar pré-natal? (SR)',
            'Motivo da visita domiciliar',
            'Observações do pré-natal',
            'O que aconteceu (investigador) - PN',
            'Responsável investigação - nome',
            'Responsável investigação - profissão',
            'Criança em acompanhamento serviço saúde? (Sim)',
            'Criança em acompanhamento serviço saúde? (Não)',
            'Criança em acompanhamento serviço saúde? (SR)',
            'Estabelecimento atendimento criança',
            'Código CNES (criança)',
            'Tipo serviço criança: CS SUS',
            'Tipo serviço criança: Convênio',
            'Tipo serviço criança: Particular',
            'Aleitamento materno? (Sim)',
            'Aleitamento materno? (Não)',
            'Aleitamento exclusivo? (Sim)',
            'Aleitamento exclusivo? (Não)',
            'Tempo aleitamento exclusivo - dias',
            'Tempo aleitamento exclusivo - meses',
            'NSA aleitamento exclusivo',
            'Duração aleitamento misto - dias',
            'Duração aleitamento misto - meses',
            'NSA aleitamento misto',
            'Observações alimentação',
            'Encaminhamento referência? (Sim)',
            'Encaminhamento referência? (Não)',
            'Encaminhamento referência? (SR)',
            'Motivo do encaminhamento',
            'Vacinação completa? (Sim)',
            'Vacinação completa? (Não)',
            'Vacinação completa? (SR)',
            'Vacinas em atraso',
            'Acompanhamento especial? (Sim)',
            'Acompanhamento especial? (Não)',
            'Acompanhamento especial? (SR)',
            'Acomp. especial: Desnutrição',
            'Acomp. especial: RN alto risco',
            'Acomp. especial: Prematuro',
            'Acomp. especial: Asma',
            'Acomp. especial: Baixo peso',
            'Acomp. especial: Outro',
            'Visitas domiciliares? (Sim)',
            'Visitas domiciliares? (Não)',
            'Visitas domiciliares? (SR)',
            'Motivo da visita domiciliar (criança)',
            'Causa do óbito no prontuário',
            'Observações gerais',
            'O que aconteceu (investigador)',
            'Data da conclusão',
            'Responsável pela investigação',
            'Responsável - carimbo/rubrica',
        ],
    }
    return campos.get(tipo, ['Observações do caso'])


def get_tipo_campo(nome_campo):
    """Retorna 'checkbox' ou 'textarea' conforme o nome do campo."""
    import re
    checkbox_re = re.compile(
        r'(?:\?\s*\()|'           # "? (" — pergunta com opção ex: (Sim), (Não), (SR)
        r'(?:^Fonte:\s)|'         # "Fonte: "
        r'(?:^Avaliação\s*\-)|'   # "Avaliação -"
        r'(?:^Organização\s*\-)|' # "Organização -"
        r'(?:^Acomp\.\s*especial:)|'  # "Acomp. especial:"
        r'(?:^Vacinação\s+tétano)|'   # "Vacinação tétano:"
        r'(?:^Esquema\s+vacinação)|'   # "Esquema vacinação tétano:"
        r'(?:^Cadastrada\s+no)|'   # "Cadastrada no Sisprenatal"
        r'(?:^Já\s+esteve)|'       # "Já esteve grávida antes?"
        r'(?:^Gestante\s+alto\s+risco)|' # "Gestante alto risco?"
        r'(?:^Acompanhada\s+PNAR)|'      # "Acompanhada PNAR?"
        r'(?:^Internada\s+(na|durante))|' # "Internada na gestação?"
        r'(?:^Uso\s+de\s+medica)|'       # "Uso de medicação?"
        r'(?:^Visita\s+domiciliar)|'      # "Visita domiciliar"
        r'(?:^Aleitamento)|'              # "Aleitamento materno?" / "Aleitamento exclusivo?"
        r'(?:^Encaminhamento\s+referência)|'  # "Encaminhamento referência?"
        r'(?:^Vacinação\s+completa)|'    # "Vacinação completa?"
        r'(?:^Acompanhamento\s+especial)|'    # "Acompanhamento especial?"
        r'(?:^Óbito\s+evitável)|'         # "Óbito evitável?"
        r'(?:^Criança\s+em\s+acompanhamento)|' # "Criança em acompanhamento serviço saúde?"
        r'(?:^Acompanhamento\s+AB)|'      # "Acompanhamento AB mantido?"
        r'(?:^Não\s+fez\s+pré-natal)|'   # "Não fez pré-natal"
        r'(?:^Sem\s+cobertura\s+ESF)'    # "Sem cobertura ESF"
    )
    if checkbox_re.search(nome_campo):
        return 'checkbox'
    # Campos com ": " seguido de opção curta
    partes = nome_campo.split(': ', 1)
    if len(partes) == 2:
        opcao = partes[1]
        palavras = opcao.split()
        if len(palavras) <= 3 and not opcao.endswith(('geral', 'prontuário', 'justificativa', 'investigação')):
            return 'checkbox'
    return 'textarea'


def get_grupo_campo(nome_campo):
    """Extrai o nome do grupo de um campo checkbox, ou None se for textarea."""
    if get_tipo_campo(nome_campo) != 'checkbox':
        return None
    import re
    # Tenta extrair prefixo antes de ": " ou "? ("
    m = re.match(r'^(.+?)\s*[:(]\s*(?:Sim|Não|SR|Ignorado|Inconclusivo|Sim/Qual|Anteparto|Intraparto|Urbana|Rural|Masculino|Feminino|CS SUS|Convênio|Particular).*', nome_campo)
    if m:
        return m.group(1).strip()
    # Para "? (" patterns
    m = re.match(r'^(.+?\?)\s*\(', nome_campo)
    if m:
        return m.group(1).strip()
    # Para ": " genérico
    partes = nome_campo.split(': ', 1)
    if len(partes) == 2:
        return partes[0]
    return nome_campo


def agrupar_campos(campos_list):
    """Agrupa campos consecutivos pelo mesmo grupo."""
    if not campos_list:
        return []
    grupos = []
    grupo_atual = None
    for campo in campos_list:
        nome = campo.nome_campo
        tipo = get_tipo_campo(nome)
        if tipo == 'checkbox':
            grp = get_grupo_campo(nome)
            if grupo_atual and grupo_atual['titulo'] == grp:
                grupo_atual['campos'].append(campo)
            else:
                grupo_atual = {'tipo': 'grupo', 'titulo': grp, 'campos': [campo]}
                grupos.append(grupo_atual)
        else:
            grupo_atual = None
            grupos.append({'tipo': 'campo', 'campo': campo})
    return grupos


# ===================== INICIALIZAÇÃO =====================
def criar_admin():
    admin = Usuario.query.filter_by(usuario='admin').first()
    if not admin:
        admin = Usuario(
            nome='Administrador',
            usuario='admin',
            cargo='Admin',
            ativo=True,
        )
        admin.set_senha('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Usuário admin criado (senha: admin123)')


with app.app_context():
    db.create_all()
    criar_admin()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
