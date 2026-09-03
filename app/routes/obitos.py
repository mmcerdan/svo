from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.forms import ObitoForm
from app.services.obito_service import ObitoService
from app.services.investigacao_service import InvestigacaoService
from app.utils.audit import audit_log
from app.utils.campos import get_campos_padrao_investigacao, agrupar_campos_list
from datetime import datetime, date

bp = Blueprint('obitos', __name__, url_prefix='/obitos')

@bp.route('/')
@login_required
def lista():
    busca = request.args.get('busca', '')
    page = request.args.get('page', 1, type=int)
    obitos = ObitoService.listar(busca=busca, page=page)
    return render_template('obitos/lista.html', obitos=obitos, busca=busca)

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    from app.models import Usuario
    form = ObitoForm(request.form if request.method == 'POST' else None)
    
    if request.method == 'POST' and form.validate():
        # Prepara dados do óbito
        dados_obito = {
            'nome': form.nome.data.strip() if form.nome.data else '',
            'data_nascimento': form.data_nascimento.data,
            'data_obito': form.data_obito.data,
            'sexo': form.sexo.data,
            'nome_mae': form.nome_mae.data.strip() if form.nome_mae.data else None,
            'nome_pai': form.nome_pai.data.strip() if form.nome_pai.data else None,
            'numero_dob': form.numero_dob.data.strip() if form.numero_dob.data else '',
            'causa_morte': form.causa_morte.data.strip() if form.causa_morte.data else None,
            'causa_morte_cid': form.causa_morte_cid.data.strip().upper() if form.causa_morte_cid.data else None,
            'local_obito': form.local_obito.data,
            'municipio_ocorrencia': form.municipio_ocorrencia.data.strip() if form.municipio_ocorrencia.data else None,
            'endereco': form.endereco.data.strip() if form.endereco.data else None,
            'observacoes': form.observacoes.data.strip() if form.observacoes.data else None,
        }
        
        tipo_investigacao = form.criar_investigacao.data or None
        dados_campos = request.form.to_dict() if tipo_investigacao else None
        
        # Cria óbito + investigação em transação única
        obito, inv, erros = InvestigacaoService.criar_com_obito(
            current_user, dados_obito, tipo_investigacao, dados_campos
        )
        
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('obitos/form.html', form=form, titulo='Novo Óbito')
        
        if inv:
            flash('Óbito cadastrado com investigação!', 'success')
            return redirect(url_for('investigacoes.detalhe', id=inv.id))
        
        flash('Óbito cadastrado com sucesso!', 'success')
        return redirect(url_for('obitos.detalhe', id=obito.id))
    
    if request.method == 'POST' and not form.validate():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('obitos/form.html', form=form, titulo='Novo Óbito')

@bp.route('/<int:id>')
@login_required
def detalhe(id):
    obito = ObitoService.buscar_por_id(id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('obitos.lista'))
    return render_template('obitos/detalhe.html', obito=obito)

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    obito = ObitoService.buscar_por_id(id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('obitos.lista'))
    
    form = ObitoForm(request.form if request.method == 'POST' else None, obj=obito)
    
    if request.method == 'POST' and form.validate():
        dados = {
            'nome': form.nome.data.strip() if form.nome.data else '',
            'data_nascimento': form.data_nascimento.data,
            'data_obito': form.data_obito.data,
            'sexo': form.sexo.data,
            'nome_mae': form.nome_mae.data.strip() if form.nome_mae.data else None,
            'nome_pai': form.nome_pai.data.strip() if form.nome_pai.data else None,
            'numero_dob': form.numero_dob.data.strip() if form.numero_dob.data else '',
            'causa_morte': form.causa_morte.data.strip() if form.causa_morte.data else None,
            'causa_morte_cid': form.causa_morte_cid.data.strip().upper() if form.causa_morte_cid.data else None,
            'local_obito': form.local_obito.data,
            'municipio_ocorrencia': form.municipio_ocorrencia.data.strip() if form.municipio_ocorrencia.data else None,
            'endereco': form.endereco.data.strip() if form.endereco.data else None,
            'observacoes': form.observacoes.data.strip() if form.observacoes.data else None,
        }
        
        erros = ObitoService.atualizar(obito, current_user, dados)
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('obitos/form.html', form=form, titulo='Editar Óbito', obito=obito)
        
        db.session.commit()
        flash('Óbito atualizado com sucesso!', 'success')
        return redirect(url_for('obitos.detalhe', id=obito.id))
    
    if request.method == 'POST' and not form.validate():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('obitos/form.html', form=form, titulo='Editar Óbito', obito=obito)

@bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    obito = ObitoService.buscar_por_id(id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('obitos.lista'))
    
    ObitoService.excluir(obito, current_user)
    db.session.commit()
    flash('Óbito excluído permanentemente.', 'success')
    return redirect(url_for('obitos.lista'))

# API para carregar campos de investigação dinamicamente
@bp.route('/api/campos-investigacao/<tipo>')
@login_required
def api_campos_investigacao(tipo):
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