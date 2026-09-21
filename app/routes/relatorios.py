from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user
from app.services.relatorio_service import RelatorioService
from datetime import datetime
import csv
import io

bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

def _extrair_filtros():
    return {
        'tipo': request.args.get('tipo', 'geral'),
        'data_inicio': request.args.get('data_inicio'),
        'data_fim': request.args.get('data_fim'),
        'nome': request.args.get('nome'),
        'idade_min': request.args.get('idade_min'),
        'idade_max': request.args.get('idade_max'),
    }

def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

def _parse_int(s):
    if not s:
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None

def _obter_dados(tipo, di, df, nome, idade_min, idade_max):
    if tipo == 'geral':
        return RelatorioService.dados_geral(di, df, nome=nome, idade_min=idade_min, idade_max=idade_max)
    elif tipo == 'investigacoes':
        return RelatorioService.dados_investigacoes(di, df, nome=nome, idade_min=idade_min, idade_max=idade_max)
    elif tipo == 'causas':
        return RelatorioService.dados_causas(di, df, nome=nome, idade_min=idade_min, idade_max=idade_max)
    return None

@bp.route('/')
@login_required
def index():
    return render_template('relatorios/index.html')

@bp.route('/dados')
@login_required
def dados():
    f = _extrair_filtros()
    di = _parse_date(f['data_inicio'])
    df = _parse_date(f['data_fim'])
    nome = f['nome'] or None
    idade_min = _parse_int(f['idade_min'])
    idade_max = _parse_int(f['idade_max'])

    resultado = _obter_dados(f['tipo'], di, df, nome, idade_min, idade_max)
    if resultado is None:
        return jsonify({'erro': 'Tipo invalido'}), 400
    return jsonify(resultado)


@bp.route('/exportar/csv')
@login_required
def exportar_csv():
    f = _extrair_filtros()
    di = _parse_date(f['data_inicio'])
    df = _parse_date(f['data_fim'])
    nome = f['nome'] or None
    idade_min = _parse_int(f['idade_min'])
    idade_max = _parse_int(f['idade_max'])
    tipo = f['tipo']

    dados = _obter_dados(tipo, di, df, nome, idade_min, idade_max)
    if dados is None:
        return jsonify({'erro': 'Tipo invalido'}), 400

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(['Relatorio', tipo.upper()])
    periodo_parts = []
    if f['data_inicio']:
        periodo_parts.append(f['De: {f["data_inicio"]}'])
    if f['data_fim']:
        periodo_parts.append(f'Ate: {f["data_fim"]}')
    if nome:
        periodo_parts.append(f'Nome: {nome}')
    if idade_min is not None:
        periodo_parts.append(f'Idade min: {idade_min}')
    if idade_max is not None:
        periodo_parts.append(f'Idade max: {idade_max}')
    writer.writerow(['Filtros', ' | '.join(periodo_parts) if periodo_parts else 'Todos'])
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
    f = _extrair_filtros()
    di = _parse_date(f['data_inicio'])
    df = _parse_date(f['data_fim'])
    nome = f['nome'] or None
    idade_min = _parse_int(f['idade_min'])
    idade_max = _parse_int(f['idade_max'])
    tipo = f['tipo']

    dados = _obter_dados(tipo, di, df, nome, idade_min, idade_max)
    if dados is None:
        return jsonify({'erro': 'Tipo invalido'}), 400

    from app.utils.pdf import _logo_data_uri
    logo_ms = _logo_data_uri('logo-ms.png')
    logo_pref = _logo_data_uri('logo.png')

    try:
        from weasyprint import HTML
        html_str = render_template('relatorios/relatorio_pdf.html',
                                   tipo=tipo, dados=dados,
                                   data_inicio=f['data_inicio'] or 'Inicio',
                                   data_fim=f['data_fim'] or 'Atual',
                                   filtros_texto=f.get('nome', ''),
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
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar PDF: {str(e)}'}), 500
