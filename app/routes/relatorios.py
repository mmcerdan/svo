from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.relatorio_service import RelatorioService
from datetime import datetime

bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@bp.route('/')
@login_required
def index():
    return render_template('relatorios/index.html')

@bp.route('/dados')
@login_required
def dados():
    tipo = request.args.get('tipo', 'geral')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    di = None
    df = None
    if data_inicio:
        di = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    if data_fim:
        df = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    if tipo == 'geral':
        dados = RelatorioService.dados_geral(di, df)
    elif tipo == 'investigacoes':
        dados = RelatorioService.dados_investigacoes(di, df)
    elif tipo == 'causas':
        dados = RelatorioService.dados_causas(di, df)
    else:
        return jsonify({'erro': 'Tipo inválido'}), 400
    
    return jsonify(dados)