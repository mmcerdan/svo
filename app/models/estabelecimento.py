from app.extensions import db
from datetime import datetime

class Estabelecimento(db.Model):
    __tablename__ = 'estabelecimentos'
    id = db.Column(db.Integer, primary_key=True)
    cnes = db.Column(db.String(7), unique=True, index=True)  # Código CNES
    nome = db.Column(db.String(200), nullable=False, index=True)
    endereco = db.Column(db.Text)
    municipio = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    tipo = db.Column(db.String(50))  # Hospital, UBS, etc.
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Estabelecimento {self.nome} (CNES: {self.cnes})>'

    def to_dict(self):
        return {
            'id': self.id,
            'cnes': self.cnes,
            'nome': self.nome,
            'endereco': self.endereco,
            'municipio': self.municipio,
            'uf': self.uf,
            'tipo': self.tipo,
            'telefone': self.telefone,
            'email': self.email,
        }