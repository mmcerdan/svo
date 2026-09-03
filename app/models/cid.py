from app.extensions import db
from datetime import datetime

class CID(db.Model):
    __tablename__ = 'cids'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, index=True, nullable=False)  # Ex: P968, P369
    descricao = db.Column(db.Text, nullable=False)
    capitulo = db.Column(db.String(100))  # Ex: "XVI - Certas afecções originadas no período perinatal"
    subcategoria = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CID {self.codigo}: {self.descricao[:50]}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'capitulo': self.capitulo,
            'subcategoria': self.subcategoria,
        }