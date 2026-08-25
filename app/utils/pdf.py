from flask import render_template, current_app
from weasyprint import HTML
from io import BytesIO
from datetime import datetime
from app.models import Investigacao
from app.services.investigacao_service import InvestigacaoService


TEMPLATE_MAP = {
    'MIF': 'investigacoes/imprimir_mif.html',
    'MATERNO': 'investigacoes/imprimir_materno.html',
    'INFANTIL_FETAL': 'investigacoes/imprimir_infantil_fetal.html',
    'MAL_DEFINIDA': 'investigacoes/imprimir_mal_definida.html',
    'INFANTIL': 'investigacoes/imprimir_infantil.html',
}


def gerar_pdf_investigacao(investigacao: Investigacao) -> bytes:
    """Gera PDF a partir do template de impressao da investigacao."""
    campos_dict = InvestigacaoService.obter_para_impressao(investigacao)
    tmpl = TEMPLATE_MAP.get(investigacao.tipo, 'investigacoes/imprimir.html')

    with current_app.app_context():
        html_string = render_template(
            tmpl,
            inv=investigacao,
            c=campos_dict,
            now=datetime.now(),
            pdf_mode=True,
        )

    base_url = current_app.static_url_path or '/static'
    pdf_bytes = HTML(string=html_string, base_url=current_app.root_path + '/..').write_pdf()

    return pdf_bytes
