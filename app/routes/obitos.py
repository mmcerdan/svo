from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.forms import ObitoForm
from app.services.obito_service import ObitoService
from app.services.investigacao_service import InvestigacaoService
from app.utils.audit import audit_log
from app.utils.campos import get_campos_padrao_investigacao, agrupar_campos_list
from app.models import Estabelecimento, CID
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
    form.estabelecimento_id.choices = [(0, 'Selecione...')] + [(e.id, f"{e.nome} ({e.municipio})") for e in Estabelecimento.query.filter_by(ativo=True).order_by(Estabelecimento.nome).all()]
    
    if request.method == 'POST' and form.validate():
        # Prepara dados do óbito
        cids = []
        for cid_form in form.causas_morte_cids.data:
            if cid_form.get('codigo'):
                cids.append({
                    'codigo': cid_form['codigo'].strip().upper(),
                    'descricao': cid_form['descricao'].strip() if cid_form.get('descricao') else ''
                })
        
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
            'causas_morte_cids': cids,
            'local_obito': form.local_obito.data,
            'municipio_ocorrencia': form.municipio_ocorrencia.data.strip() if form.municipio_ocorrencia.data else None,
            'endereco': form.endereco.data.strip() if form.endereco.data else None,
            'observacoes': form.observacoes.data.strip() if form.observacoes.data else None,
            'estabelecimento_id': form.estabelecimento_id.data if form.estabelecimento_id.data else None,
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
    form.estabelecimento_id.choices = [(0, 'Selecione...')] + [(e.id, f"{e.nome} ({e.municipio})") for e in Estabelecimento.query.filter_by(ativo=True).order_by(Estabelecimento.nome).all()]
    
    # Pre-populate CIDs from existing data
    if request.method == 'GET' and obito.causas_morte_cids:
        # Clear default entry and populate with existing
        pass  # WTForms will handle via obj=obito
    
    if request.method == 'POST' and form.validate():
        cids = []
        for cid_form in form.causas_morte_cids.data:
            if cid_form.get('codigo'):
                cids.append({
                    'codigo': cid_form['codigo'].strip().upper(),
                    'descricao': cid_form['descricao'].strip() if cid_form.get('descricao') else ''
                })
        
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
            'causas_morte_cids': cids,
            'local_obito': form.local_obito.data,
            'municipio_ocorrencia': form.municipio_ocorrencia.data.strip() if form.municipio_ocorrencia.data else None,
            'endereco': form.endereco.data.strip() if form.endereco.data else None,
            'observacoes': form.observacoes.data.strip() if form.observacoes.data else None,
            'estabelecimento_id': form.estabelecimento_id.data if form.estabelecimento_id.data else None,
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

# API: Busca de CIDs
@bp.route('/api/cid/buscar')
@login_required
def api_cid_buscar():
    q = request.args.get('q', '').strip().upper()
    if not q or len(q) < 2:
        return jsonify({'cids': []})
    
    cids = CID.query.filter(
        db.or_(
            CID.codigo.ilike(f'%{q}%'),
            CID.descricao.ilike(f'%{q}%')
        )
    ).filter_by(ativo=True).limit(20).all()
    
    return jsonify({'cids': [c.to_dict() for c in cids]})

# API: Estabelecimentos
@bp.route('/api/estabelecimentos')
@login_required
def api_estabelecimentos():
    q = request.args.get('q', '').strip()
    query = Estabelecimento.query.filter_by(ativo=True)
    if q:
        query = query.filter(
            db.or_(
                Estabelecimento.nome.ilike(f'%{q}%'),
                Estabelecimento.cnes.ilike(f'%{q}%'),
                Estabelecimento.municipio.ilike(f'%{q}%')
            )
        )
    estabs = query.order_by(Estabelecimento.nome).limit(50).all()
    return jsonify({'estabelecimentos': [e.to_dict() for e in estabs]})

@bp.route('/api/estabelecimentos', methods=['POST'])
@login_required
def api_estabelecimento_criar():
    from app.utils.security import admin_required
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    data = request.get_json() or {}
    required = ['nome']
    for field in required:
        if not data.get(field):
            return jsonify({'erro': f'Campo obrigatório: {field}'}), 400
    
    estab = Estabelecimento(
        cnes=data.get('cnes', '').strip() or None,
        nome=data['nome'].strip(),
        endereco=data.get('endereco', '').strip() or None,
        municipio=data.get('municipio', '').strip() or None,
        uf=data.get('uf', '').strip().upper() or None,
        tipo=data.get('tipo', '').strip() or None,
        telefone=data.get('telefone', '').strip() or None,
        email=data.get('email', '').strip() or None,
    )
    db.session.add(estab)
    db.session.commit()
    return jsonify(estab.to_dict()), 201

@bp.route('/api/estabelecimentos/<int:id>', methods=['PUT'])
@login_required
def api_estabelecimento_atualizar(id):
    from app.utils.security import admin_required
    if not current_user.is_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    estab = db.session.get(Estabelecimento, id)
    if not estab:
        return jsonify({'erro': 'Não encontrado'}), 404
    
    data = request.get_json() or {}
    for field in ['cnes', 'nome', 'endereco', 'municipio', 'uf', 'tipo', 'telefone', 'email', 'ativo']:
        if field in data:
            setattr(estab, field, data[field])
    
    db.session.commit()
    return jsonify(estab.to_dict())