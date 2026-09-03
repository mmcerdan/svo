from app.extensions import db
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSONB

class Obito(db.Model):
    __tablename__ = 'obitos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    data_nascimento = db.Column(db.Date, index=True)
    data_obito = db.Column(db.Date, nullable=False, index=True)
    sexo = db.Column(db.String(1))
    nome_mae = db.Column(db.String(200))
    nome_pai = db.Column(db.String(200))
    numero_dob = db.Column(db.String(50), unique=True, index=True)
    causa_morte = db.Column(db.Text)
    causa_morte_cid = db.Column(db.String(10), index=True)
    causas_morte_cids = db.Column(JSONB, default=list)  # Lista de CIDs: [{"cid": "P968", "descricao": "..."}, ...]
    local_obito = db.Column(db.String(50))
    municipio_ocorrencia = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', backref='obitos')
    estabelecimento_id = db.Column(db.Integer, db.ForeignKey('estabelecimentos.id'))
    estabelecimento = db.relationship('Estabelecimento', backref='obitos')

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
        return self.investigacoes.order_by(db.desc('criado_em')).first()

    def __repr__(self):
        return f'<Obito {self.nome} - DO:{self.numero_dob}>'