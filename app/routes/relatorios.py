from flask import Blueprint, render_template, request, jsonify, make_response, send_file
from flask_login import login_required, current_user
from app.services.relatorio_service import RelatorioService
from app.utils.pdf import _logo_data_uri
from datetime import datetime
import csv
import io

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
    
    di = _parse_date(data_inicio)
    df = _parse_date(data_fim)
    
    if tipo == 'geral':
        resultado = RelatorioService.dados_geral(di, df)
    elif tipo == 'investigacoes':
        resultado = RelatorioService.dados_investigacoes(di, df)
    elif tipo == 'causas':
        resultado = RelatorioService.dados_causas(di, df)
    else:
        return jsonify({'erro': 'Tipo invalido'}), 400
    
    return jsonify(resultado)


@bp.route('/exportar/csv')
@login_required
def exportar_csv():
    tipo = request.args.get('tipo', 'geral')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    di = _parse_date(data_inicio)
    df = _parse_date(data_fim)
    
    if tipo == 'geral':
        dados = RelatorioService.dados_geral(di, df)
    elif tipo == 'investigacoes':
        dados = RelatorioService.dados_investigacoes(di, df)
    elif tipo == 'causas':
        dados = RelatorioService.dados_causas(di, df)
    else:
        return jsonify({'erro': 'Tipo invalido'}), 400
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    writer.writerow(['Relatorio', tipo.upper()])
    writer.writerow(['Periodo', f'{data_inicio or "Inicio"} a {data_fim or "Atual"}'])
    writer.writerow(['Gerado em', datetime.now().strftime('%d/%m/%Y %H:%M')])
    writer.writerow([])
    
    if tipo == 'geral':
        writer.writerow(['Resumo Geral'])
        writer.writerow(['Total de obitos', dados['total']])
        writer.writerow([])
        writer.writerow(['Por Sexo', 'Quantidade'])
        for item in dados['por_sexo']:
            writer.writerow([item['label'], item['value']])
        writer.writerow([])
        writer.writerow(['Por Local', 'Quantidade'])
        for item in dados['por_local']:
            writer.writerow([item['label'], item['value']])
    
    elif tipo == 'investigacoes':
        writer.writerow(['Investigacoes'])
        writer.writerow(['Total', dados['total']])
        writer.writerow([])
        writer.writerow(['Por Tipo', 'Quantidade'])
        for item in dados['por_tipo']:
            writer.writerow([item['label'], item['value']])
        writer.writerow([])
        writer.writerow(['Por Status', 'Quantidade'])
        for item in dados['por_status']:
            writer.writerow([item['label'], item['value']])
    
    elif tipo == 'causas':
        writer.writerow(['Causas de Obito (CID-10)'])
        writer.writerow([])
        writer.writerow(['CID-10', 'Descricao', 'Quantidade'])
        for item in dados['causas']:
            writer.writerow([item['label'], item.get('descricao', ''), item['value']])
    
    filename = f'relatorio_{tipo}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Cache-Control'] = 'no-cache'
    output.close()
    
    return response


@bp.route('/exportar/pdf')
@login_required
def exportar_pdf():
    tipo = request.args.get('tipo', 'geral')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    di = _parse_date(data_inicio)
    df = _parse_date(data_fim)
    
    if tipo == 'geral':
        dados = RelatorioService.dados_geral(di, df)
    elif tipo == 'investigacoes':
        dados = RelatorioService.dados_investigacoes(di, df)
    elif tipo == 'causas':
        dados = RelatorioService.dados_causas(di, df)
    else:
        return jsonify({'erro': 'Tipo invalido'}), 400
    
    logo_ms = _logo_data_uri('logo-ms.png')
    logo_pref = _logo_data_uri('logo.png')
    
    from weasyprint import HTML
    html_str = render_template('relatorios/relatorio_pdf.html',
                               tipo=tipo, dados=dados,
                               data_inicio=data_inicio or 'Inicio',
                               data_fim=data_fim or 'Atual',
                               logo_ms=logo_ms, logo_pref=logo_pref,
                               now=datetime.now(),
                               usuario=current_user.nome)
    
    pdf_bytes = HTML(string=html_str).write_pdf()
    
    filename = f'relatorio_{tipo}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Cache-Control'] = 'no-cache'
    
    return response


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None