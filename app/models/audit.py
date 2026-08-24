from app.extensions import db
from datetime import datetime
import json

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), index=True)
    usuario_nome = db.Column(db.String(100))
    acao = db.Column(db.String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, PRINT, EXPORT
    entidade = db.Column(db.String(50), nullable=False, index=True)  # Obito, Investigacao, Usuario, Anexo
    entidade_id = db.Column(db.Integer, index=True)
    dados_antes = db.Column(db.Text)  # JSON
    dados_depois = db.Column(db.Text)  # JSON
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index('ix_audit_entidade_data', 'entidade', 'criado_em'),
        db.Index('ix_audit_usuario_data', 'usuario_id', 'criado_em'),
    )

    @staticmethod
    def log(usuario, acao, entidade, entidade_id=None, dados_antes=None, dados_depois=None, request=None):
        """Registra ação de auditoria"""
        try:
            log = AuditLog(
                usuario_id=usuario.id if usuario else None,
                usuario_nome=usuario.nome if usuario else 'Sistema',
                acao=acao,
                entidade=entidade,
                entidade_id=entidade_id,
                dados_antes=json.dumps(dados_antes, ensure_ascii=False, default=str) if dados_antes else None,
                dados_depois=json.dumps(dados_depois, ensure_ascii=False, default=str) if dados_depois else None,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent') if request else None,
            )
            db.session.add(log)
            return log
        except Exception:
            # Não falha a operação principal por erro de auditoria
            pass