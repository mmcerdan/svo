from app.extensions import db
from app.models import AuditLog
from flask import request
import json
from datetime import datetime

def audit_log(usuario, acao: str, entidade: str, entidade_id: int = None, 
              dados_antes: dict = None, dados_depois: dict = None):
    """
    Registra ação de auditoria para LGPD/trilha de auditoria.
    Não falha a operação principal se a auditoria falhar.
    """
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
    except Exception as e:
        # Log interno mas não falha a operação
        current_app.logger.warning(f'Falha ao registrar auditoria: {e}')

def serialize_model(obj, exclude=None) -> dict:
    """Serializa modelo SQLAlchemy para dict."""
    if not obj:
        return None
    exclude = exclude or ['senha_hash']
    data = {}
    for col in obj.__table__.columns:
        if col.name not in exclude:
            val = getattr(obj, col.name)
            if isinstance(val, datetime):
                data[col.name] = val.isoformat()
            else:
                data[col.name] = val
    return data