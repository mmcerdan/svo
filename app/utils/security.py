from functools import wraps
from flask import request, abort, current_app
from flask_login import current_user
import re

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.cargo not in ('Admin', 'Supervisor'):
            abort(403, description='Acesso restrito a administradores.')
        return f(*args, **kwargs)
    return decorated

def supervisor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.cargo not in ('Admin', 'Supervisor'):
            abort(403, description='Acesso restrito a supervisores.')
        return f(*args, **kwargs)
    return decorated

def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitiza entrada de texto para prevenir XSS."""
    if not text:
        return ''
    # Remove scripts e eventos
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=\s*\S+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text[:max_length]

def sanitize_html(text: str) -> str:
    """Escapa HTML para exibição segura."""
    if not text:
        return ''
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )

def validate_file_upload(file, allowed_extensions=None, max_size_mb=16) -> tuple[bool, str]:
    """Valida upload de arquivo."""
    if not file or not file.filename:
        return False, 'Nenhum arquivo selecionado.'
    
    if allowed_extensions:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            return False, f'Extensão não permitida. Permitidas: {", ".join(allowed_extensions)}'
    
    # Verifica tamanho (aproximado via content_length)
    if request.content_length and request.content_length > max_size_mb * 1024 * 1024:
        return False, f'Arquivo excede {max_size_mb}MB.'
    
    return True, ''

def generate_csrf_token() -> str:
    """Gera token CSRF (usa Flask-WTF internamente)."""
    from flask_wtf.csrf import generate_csrf
    return generate_csrf()

def verify_csrf_token(token: str) -> bool:
    """Verifica token CSRF."""
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
        return True
    except:
        return False