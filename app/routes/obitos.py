from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
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
    from wtforms import Form
    
    if request.method == 'POST':
        # Prepara dados do óbito
        dados_obito = {
            'nome': request.form.get('nome', '').strip(),
            'data_nascimento': request.form.get('data_nascimento') or None,
            'data_obito': request.form.get('data_obito'),
            'sexo': request.form.get('sexo') or None,
            'nome_mae': request.form.get('nome_mae', '').strip() or None,
            'nome_pai': request.form.get('nome_pai', '').strip() or None,
            'numero_dob': request.form.get('numero_dob', '').strip(),
            'causa_morte': request.form.get('causa_morte', '').strip() or None,
            'causa_morte_cid': request.form.get('causa_morte_cid', '').strip().upper() or None,
            'local_obito': request.form.get('local_obito') or None,
            'municipio_ocorrencia': request.form.get('municipio_ocorrencia', '').strip() or None,
            'endereco': request.form.get('endereco', '').strip() or None,
            'observacoes': request.form.get('observacoes', '').strip() or None,
        }
        
        tipo_investigacao = request.form.get('criar_investigacao') or None
        dados_campos = request.form.to_dict() if tipo_investigacao else None
        
        # Cria óbito + investigação em transação única
        obito, inv, erros = InvestigacaoService.criar_com_obito(
            current_user, dados_obito, tipo_investigacao, dados_campos
        )
        
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('obitos/form.html', 
                                   form=Form(request.form), 
                                   titulo='Novo Óbito')
        
        if inv:
            flash('Óbito cadastrado com investigação!', 'success')
            return redirect(url_for('investigacoes.detalhe', id=inv.id))
        
        flash('Óbito cadastrado com sucesso!', 'success')
        return redirect(url_for('obitos.detalhe', id=obito.id))
    
    # GET - renderiza formulário
    from app.forms import ObitoForm
    form = ObitoForm()
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
    from app.forms import ObitoForm
    obito = ObitoService.buscar_por_id(id)
    if not obito:
        flash('Óbito não encontrado.', 'danger')
        return redirect(url_for('obitos.lista'))
    
    if request.method == 'POST':
        dados = {
            'nome': request.form.get('nome', '').strip(),
            'data_nascimento': request.form.get('data_nascimento') or None,
            'data_obito': request.form.get('data_obito'),
            'sexo': request.form.get('sexo') or None,
            'nome_mae': request.form.get('nome_mae', '').strip() or None,
            'nome_pai': request.form.get('nome_pai', '').strip() or None,
            'numero_dob': request.form.get('numero_dob', '').strip(),
            'causa_morte': request.form.get('causa_morte', '').strip() or None,
            'causa_morte_cid': request.form.get('causa_morte_cid', '').strip().upper() or None,
            'local_obito': request.form.get('local_obito') or None,
            'municipio_ocorrencia': request.form.get('municipio_ocorrencia', '').strip() or None,
            'endereco': request.form.get('endereco', '').strip() or None,
            'observacoes': request.form.get('observacoes', '').strip() or None,
        }
        
        erros = ObitoService.atualizar(obito, current_user, dados)
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('obitos/form.html', form=ObitoForm(request.form, obj=obito), 
                                   titulo='Editar Óbito', obito=obito)
        
        db.session.commit()
        flash('Óbito atualizado com sucesso!', 'success')
        return redirect(url_for('obitos.detalhe', id=obito.id))
    
    form = ObitoForm(obj=obito)
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