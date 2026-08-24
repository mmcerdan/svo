import os
from flask import Flask, render_template, request
from app.config import config
from app.extensions import init_extensions
from app.routes import register_blueprints
from app.models import Usuario
from app.utils.campos import get_tipo_campo, agrupar_campos

def create_app(config_name=None):
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Garante pasta de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    init_extensions(app)
    register_blueprints(app)
    
    # Context processors
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now(), 'get_tipo_campo': get_tipo_campo, 'agrupar_campos': agrupar_campos}
    
    # Login manager
    from app.extensions import login_manager
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html', error=e), 400
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', error=e), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html', error=e), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html', error=e), 500
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # CSP - Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        # HSTS para produção
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Cria tabelas
    with app.app_context():
        from app.extensions import db
        db.create_all()
        # Cria admin padrão
        admin = Usuario.query.filter_by(usuario='admin').first()
        if not admin:
            admin = Usuario(nome='Administrador', usuario='admin', cargo='Admin', ativo=True)
            admin.set_senha(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Usuário admin criado')
    
    return app