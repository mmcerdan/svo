from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, session, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Investigacao, InvestigacaoCampo, Anexo, Obito
from app.services.investigacao_service import InvestigacaoService
from app.utils.audit import audit_log, serialize_model
from app.utils.campos import get_campos_padrao_investigacao, get_tipo_campo, get_grupo_campo, agrupar_campos
from app.utils.validators import ValidadorInvestigacao
from app.utils.security import validate_file_upload
from app.utils.campos import agrupar_campos as agrupar_campos_util
from datetime import datetime, date
import uuid
import os
import hashlib
from werkzeug.utils import secure_filename

bp = Blueprint('investigacoes', __name__, url_prefix='/investigacoes')

def _validar_csrf():
    from flask_wtf.csrf import validate_csrf
    token = request.form.get('csrf_token', '')
    try:
        validate_csrf(token)
    except Exception:
        abort(403)

@bp.route('/')
@login_required
def lista():
    from app.models import TIPOS_INVESTIGACAO, STATUS_INVESTIGACAO
    tipo = request.args.get('tipo', '')
    status = request.args.get('status', '')
    busca = request.args.get('busca', '')
    page = request.args.get('page', 1, type=int)
    
    investigacoes = InvestigacaoService.listar(tipo=tipo, status=status, busca=busca, page=page)
    return render_template('investigacoes/lista.html', investigacoes=investigacoes,
                           tipo=tipo, status=status, busca=busca,
                           tipos_inv=TIPOS_INVESTIGACAO,
                           status_inv=STATUS_INVESTIGACAO)

@bp.route('/<int:obito_id>/nova', methods=['GET', 'POST'])
@login_required
def nova(obito_id):
    from app.models import Obito
    from app.forms import InvestigacaoForm
    from app.models import TIPOS_INVESTIGACAO
    
    obito = db.session.get(Obito, obito_id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('obitos.lista'))
    
    if request.method == 'POST':
        form = InvestigacaoForm(request.form)
        if not form.validate():
            flash('Erro de validação. Verifique os campos.', 'danger')
            return render_template('investigacoes/form.html', form=form, obito=obito, titulo='Nova Investigação')
        
        tipo = form.tipo.data
        tipos_validos = [k for k, v in TIPOS_INVESTIGACAO]
        if tipo not in tipos_validos:
            flash('Tipo de investigação inválido.', 'danger')
            return render_template('investigacoes/form.html', form=form, obito=obito, titulo='Nova Investigação')
        
        inv = Investigacao(
            obito_id=obito.id,
            tipo=tipo,
            status=form.status.data or 'AGUARDANDO',
            responsavel=form.responsavel.data or None,
            data_abertura=form.data_abertura.data or date.today(),
            data_conclusao=form.data_conclusao.data or None,
            conclusao=form.conclusao.data.strip() if form.conclusao.data else None,
            observacoes=form.observacoes.data.strip() if form.observacoes.data else None,
            usuario_id=current_user.id,
        )
        db.session.add(inv)
        db.session.flush()
        
        # Cria campos padrão preenchidos do obito
        campos_padrao = get_campos_padrao_investigacao(inv.tipo)
        valores = InvestigacaoService._preencher_de_obito(campos_padrao, obito)
        for nome_campo in campos_padrao:
            campo = InvestigacaoCampo(
                investigacao_id=inv.id, 
                nome_campo=nome_campo, 
                valor=valores.get(nome_campo, '')
            )
            db.session.add(campo)
        
        db.session.commit()
        flash('Investigação criada com sucesso!', 'success')
        return redirect(url_for('investigacoes.detalhe', id=inv.id))
    
    form = InvestigacaoForm()
    return render_template('investigacoes/form.html', form=form, obito=obito, titulo='Nova Investigação')

# API para campos por tipo (usado no formulário de óbito)
@bp.route('/campos-por-tipo/<tipo>')
@login_required
def campos_por_tipo(tipo):
    from app.utils.campos import get_campos_padrao_investigacao, get_tipo_campo, get_grupo_campo, agrupar_campos_list
    
    if tipo not in ['MIF', 'MATERNO', 'INFANTIL_FETAL', 'MAL_DEFINIDA', 'INFANTIL']:
        return jsonify({'erro': 'Tipo inválido'}), 400
    
    campos = get_campos_padrao_investigacao(tipo)
    items = []
    for nome in campos:
        items.append({
            'nome': nome,
            'tipo': get_tipo_campo(nome),
            'grupo': get_grupo_campo(nome),
        })
    grupos = agrupar_campos_list(items)
    return jsonify({'campos': items, 'grupos': grupos})

@bp.route('/<int:id>')
@login_required
def detalhe(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    return render_template('investigacoes/detalhe.html', inv=inv)

@bp.route('/<int:id>/imprimir')
@login_required
def imprimir(id):
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    
    campos_dict = InvestigacaoService.obter_para_impressao(inv)
    
    from app.utils.pdf import _logo_data_uri
    logo_ms = _logo_data_uri('logo-ms.png')
    logo_pref = _logo_data_uri('logo.png')

    template_map = {
        'MIF': 'investigacoes/imprimir_mif.html',
        'MATERNO': 'investigacoes/imprimir_materno.html',
        'INFANTIL_FETAL': 'investigacoes/imprimir_infantil_fetal.html',
        'MAL_DEFINIDA': 'investigacoes/imprimir_mal_definida.html',
        'INFANTIL': 'investigacoes/imprimir_infantil.html',
    }
    tmpl = template_map.get(inv.tipo, 'investigacoes/imprimir.html')
    return render_template(tmpl, inv=inv, c=campos_dict, now=datetime.now(),
                           logo_ms=logo_ms, logo_pref=logo_pref)

@bp.route('/<int:id>/pdf')
@login_required
def pdf(id):
    from flask import make_response
    from app.utils.pdf import gerar_pdf_investigacao
    
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    
    try:
        pdf_bytes = gerar_pdf_investigacao(inv)
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=investigacao_{inv.id}_{inv.tipo}.pdf'
        return response
    except Exception as e:
        current_app.logger.error(f'Erro ao gerar PDF: {e}')
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('investigacoes.detalhe', id=inv.id))

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    from app.forms import InvestigacaoForm
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    
    if request.method == 'POST':
        form = InvestigacaoForm(request.form)
        if not form.validate():
            flash('Erro de validação. Verifique os campos.', 'danger')
        else:
            erros = InvestigacaoService.atualizar_status(inv, current_user, {
                'status': form.status.data,
                'responsavel': form.responsavel.data,
                'data_abertura': form.data_abertura.data.strftime('%Y-%m-%d') if form.data_abertura.data else None,
                'data_conclusao': form.data_conclusao.data.strftime('%Y-%m-%d') if form.data_conclusao.data else None,
                'conclusao': form.conclusao.data,
                'observacoes': form.observacoes.data,
            })
            if erros:
                for erro in erros:
                    flash(erro, 'danger')
            else:
                flash('Investigação atualizada!', 'success')
                return redirect(url_for('investigacoes.detalhe', id=inv.id))
    
    form = InvestigacaoForm(obj=inv)
    return render_template('investigacoes/form.html', form=form, obito=inv.obito,
                           titulo='Editar Investigação', inv=inv)

@bp.route('/<int:id>/finalizar', methods=['POST'])
@login_required
def finalizar(id):
    _validar_csrf()
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    
    conclusao = request.form.get('conclusao', '').strip()
    erros = InvestigacaoService.finalizar(inv, current_user, conclusao)
    
    if erros:
        for erro in erros:
            flash(erro, 'danger')
    else:
        flash('Investigação concluída com sucesso!', 'success')
    
    return redirect(url_for('investigacoes.detalhe', id=inv.id))

@bp.route('/<int:id>/salvar-campos', methods=['POST'])
@login_required
def salvar_campos(id):
    _validar_csrf()
    inv = db.session.get(Investigacao, id)
    if not inv:
        return jsonify({'erro': 'Investigação não encontrada'}), 404
    
    erros = InvestigacaoService.atualizar_campos(inv, current_user, request.form)
    if erros:
        return jsonify({'erros': erros}), 400
    
    # Validação específica do tipo
    erros_val = ValidadorInvestigacao.validar(inv.tipo, {
        c.nome_campo: c.valor for c in inv.campos
    })
    if erros_val:
        return jsonify({'erros': erros_val, 'aviso': True}), 200
    
    return jsonify({'sucesso': True, 'mensagem': 'Campos salvos com sucesso!'})

@bp.route('/<int:id>/anexar', methods=['POST'])
@login_required
def anexar_arquivo(id):
    _validar_csrf()
    inv = db.session.get(Investigacao, id)
    if not inv:
        flash('Investigação não encontrada.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('investigacoes.detalhe', id=inv.id))
    
    arquivo = request.files['arquivo']
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('investigacoes.detalhe', id=inv.id))
    
    ok, msg = validate_file_upload(arquivo, allowed_extensions={'pdf', 'jpg', 'jpeg', 'png'})
    if not ok:
        flash(msg, 'danger')
        return redirect(url_for('investigacoes.detalhe', id=inv.id))
    
    ext = arquivo.filename.rsplit('.', 1)[-1].lower() if '.' in arquivo.filename else ''
    nome_arquivo = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    arquivo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo))
    
    anexo = Anexo(
        investigacao_id=inv.id,
        nome_original=secure_filename(arquivo.filename) or arquivo.filename,
        nome_arquivo=nome_arquivo,
        tipo=ext,
        tamanho=os.path.getsize(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)),
    )
    db.session.add(anexo)
    db.session.commit()
    
    from app.utils.audit import audit_log
    audit_log(current_user, 'UPLOAD', 'Anexo', anexo.id,
              None, {'nome': anexo.nome_original, 'tipo': ext})
    
    flash('Arquivo anexado com sucesso!', 'success')
    return redirect(url_for('investigacoes.detalhe', id=inv.id))

@bp.route('/download/<nome_arquivo>')
@login_required
def download_anexo(nome_arquivo):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], nome_arquivo)

@bp.route('/anexos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_anexo(id):
    _validar_csrf()
    anexo = db.session.get(Anexo, id)
    if not anexo:
        flash('Anexo não encontrado.', 'danger')
        return redirect(url_for('investigacoes.lista'))
    
    inv_id = anexo.investigacao_id
    caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], anexo.nome_arquivo)
    if os.path.exists(caminho):
        os.remove(caminho)
    
    from app.utils.audit import audit_log
    audit_log(current_user, 'DELETE', 'Anexo', anexo.id,
              {'nome': anexo.nome_original}, None)
    
    db.session.delete(anexo)
    db.session.commit()
    flash('Anexo excluído.', 'success')
    return redirect(url_for('investigacoes.detalhe', id=inv_id))

# API para salvar campos via AJAX
@bp.route('/<int:id>/salvar-campos-ajax', methods=['POST'])
@login_required
def salvar_campos_ajax(id):
    _validar_csrf()
    inv = db.session.get(Investigacao, id)
    if not inv:
        return jsonify({'erro': 'Investigação não encontrada'}), 404
    
    erros = InvestigacaoService.atualizar_campos(inv, current_user, request.form)
    if erros:
        return jsonify({'erros': erros}), 400
    
    return jsonify({'sucesso': True, 'mensagem': 'Campos salvos com sucesso!'})