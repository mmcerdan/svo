from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Obito, Investigacao
from app.services.relatorio_service import RelatorioService

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    total_obitos = Obito.query.count()
    total_investigacoes = Investigacao.query.count()
    pendentes = Investigacao.query.filter_by(status='AGUARDANDO').count()
    concluidas = Investigacao.query.filter_by(status='CONCLUIDA').count()
    ultimos_obitos = Obito.query.order_by(Obito.criado_em.desc()).limit(5).all()
    
    from app.models import TIPOS_INVESTIGACAO
    inv_tipos = []
    for k, v in TIPOS_INVESTIGACAO:
        count = Investigacao.query.filter_by(tipo=k).count()
        inv_tipos.append({'tipo': k, 'descricao': v, 'count': count})
    
    return render_template('index.html', total_obitos=total_obitos,
                           total_investigacoes=total_investigacoes,
                           pendentes=pendentes, concluidas=concluidas,
                           ultimos_obitos=ultimos_obitos, inv_tipos=inv_tipos)

# Health check endpoint
@bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}, 200

from datetime import datetime