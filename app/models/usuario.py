from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(50), default='Usuário', nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)

    def set_senha(self, senha):
        if len(senha) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f'<Usuario {self.usuario}>'

    def is_admin(self):
        return self.cargo in ('Admin', 'Supervisor')