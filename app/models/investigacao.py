from app.extensions import db
from datetime import datetime, date

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

class Investigacao(db.Model):
    __tablename__ = 'investigacoes'
    id = db.Column(db.Integer, primary_key=True)
    obito_id = db.Column(db.Integer, db.ForeignKey('obitos.id'), nullable=False, index=True)
    tipo = db.Column(db.String(30), nullable=False, index=True)
    status = db.Column(db.String(20), default='AGUARDANDO', nullable=False, index=True)
    responsavel = db.Column(db.String(100))
    data_abertura = db.Column(db.Date, default=date.today)
    data_conclusao = db.Column(db.Date)
    conclusao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
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

    def __repr__(self):
        return f'<Investigacao {self.tipo} - {self.status}>'

class InvestigacaoCampo(db.Model):
    __tablename__ = 'investigacao_campos'
    id = db.Column(db.Integer, primary_key=True)
    investigacao_id = db.Column(db.Integer, db.ForeignKey('investigacoes.id'), nullable=False, index=True)
    nome_campo = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_investigacao_campo_nome', 'investigacao_id', 'nome_campo'),
    )

class Anexo(db.Model):
    __tablename__ = 'anexos'
    id = db.Column(db.Integer, primary_key=True)
    investigacao_id = db.Column(db.Integer, db.ForeignKey('investigacoes.id'), nullable=False, index=True)
    nome_original = db.Column(db.String(200))
    nome_arquivo = db.Column(db.String(200))
    tipo = db.Column(db.String(50))
    tamanho = db.Column(db.Integer)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Anexo {self.nome_original}>'