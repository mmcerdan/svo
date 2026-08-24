from app.routes.main import bp as main_bp
from app.routes.auth import bp as auth_bp
from app.routes.obitos import bp as obitos_bp
from app.routes.investigacoes import bp as investigacoes_bp
from app.routes.relatorios import bp as relatorios_bp
from app.routes.admin import bp as admin_bp

def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(obitos_bp)
    app.register_blueprint(investigacoes_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(admin_bp)