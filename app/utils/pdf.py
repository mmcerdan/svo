import base64
import os
from flask import render_template, current_app
from weasyprint import HTML
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

_LOGO_CACHE = {}


def _logo_data_uri(filename):
    if filename in _LOGO_CACHE:
        return _LOGO_CACHE[filename]
    app = current_app._get_current_object()
    path = os.path.join(app.root_path, 'static', filename)
    if not os.path.isfile(path):
        _LOGO_CACHE[filename] = ''
        return ''
    with open(path, 'rb') as f:
        raw = f.read()
    ext = filename.rsplit('.', 1)[-1].lower()
    mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'gif': 'image/gif', 'svg': 'image/svg+xml'}.get(ext, 'image/png')
    uri = f'data:{mime};base64,{base64.b64encode(raw).decode()}'
    _LOGO_CACHE[filename] = uri
    return uri


def gerar_pdf_investigacao(investigacao: Investigacao) -> bytes:
    campos_dict = InvestigacaoService.obter_para_impressao(investigacao)
    tmpl = TEMPLATE_MAP.get(investigacao.tipo, 'investigacoes/imprimir.html')

    logo_ms = _logo_data_uri('logo-ms.png')
    logo_pref = _logo_data_uri('logo.png')

    app = current_app._get_current_object()
    with app.test_request_context():
        html_string = render_template(
            tmpl,
            inv=investigacao,
            c=campos_dict,
            now=datetime.now(),
            pdf_mode=True,
            logo_ms=logo_ms,
            logo_pref=logo_pref,
        )

    base_url = app.root_path + '/..'
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

    return pdf_bytes
