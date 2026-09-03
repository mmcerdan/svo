from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, PasswordField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, Length

LOCAIS_OBITO = [
    ('HOSPITAL', 'Hospital'),
    ('DOMICILIO', 'Domicílio'),
    ('VIA_PUBLICA', 'Via Pública'),
    ('OUTROS', 'Outros'),
]

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

class CIDForm(FlaskForm):
    codigo = StringField('CID', validators=[Optional(), Length(max=10)])
    descricao = StringField('Descrição', validators=[Optional(), Length(max=300)])

class LoginForm(FlaskForm):
    usuario = StringField('Usuário', validators=[DataRequired(), Length(max=50)])
    senha = PasswordField('Senha', validators=[DataRequired()])

class ObitoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    data_nascimento = DateField('Data de Nascimento', validators=[Optional()], format='%Y-%m-%d')
    data_obito = DateField('Data do Óbito', validators=[DataRequired()], format='%Y-%m-%d')
    sexo = SelectField('Sexo', choices=[('', 'Selecione...'), ('M', 'Masculino'), ('F', 'Feminino')],
                       validators=[Optional()])
    nome_mae = StringField('Nome da Mãe', validators=[Optional(), Length(max=200)])
    nome_pai = StringField('Nome do Pai', validators=[Optional(), Length(max=200)])
    numero_dob = StringField('Nº Declaração de Óbito', validators=[Optional(), Length(max=50)])
    causa_morte = TextAreaField('Causa da Morte', validators=[Optional()])
    causa_morte_cid = StringField('CID Principal da Causa da Morte', validators=[Optional(), Length(max=10)])
    causas_morte_cids = FieldList(FormField(CIDForm), min_entries=1)  # Múltiplos CIDs
    local_obito = SelectField('Local do Óbito', choices=[('', 'Selecione...')] + LOCAIS_OBITO,
                              validators=[Optional()])
    municipio_ocorrencia = StringField('Município da Ocorrência', validators=[Optional(), Length(max=100)])
    endereco = TextAreaField('Endereço', validators=[Optional()])
    observacoes = TextAreaField('Observações', validators=[Optional()])
    estabelecimento_id = SelectField('Estabelecimento', coerce=int, validators=[Optional()],
                                      choices=[(0, 'Selecione...')])
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
    data_abertura = DateField('Data de Abertura', validators=[Optional()], format='%Y-%m-%d')
    data_conclusao = DateField('Data de Conclusão', validators=[Optional()], format='%Y-%m-%d')
    conclusao = TextAreaField('Conclusão', validators=[Optional()])
    observacoes = TextAreaField('Observações', validators=[Optional()])