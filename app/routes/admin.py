from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Usuario
from app.utils.security import admin_required, sanitize_input
from app.utils.audit import audit_log
from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', ''))
        usuario = sanitize_input(request.form.get('usuario', ''))
        senha = request.form.get('senha', '')
        cargo = request.form.get('cargo', 'Usuário')
        
        erros = []
        if not nome:
            erros.append('Nome é obrigatório.')
        if not usuario:
            erros.append('Usuário é obrigatório.')
        if not senha:
            erros.append('Senha é obrigatória.')
        elif len(senha) < 8:
            erros.append('Senha deve ter no mínimo 8 caracteres.')
        
        if Usuario.query.filter_by(usuario=usuario).first():
            erros.append('Nome de usuário já existe.')
        
        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('admin_usuario_form.html')
        
        u = Usuario(nome=nome, usuario=usuario, cargo=cargo)
        u.set_senha(senha)
        db.session.add(u)
        db.session.commit()
        
        audit_log(current_user, 'CREATE', 'Usuario', u.id,
                  None, {'nome': nome, 'usuario': usuario, 'cargo': cargo}, request)
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('admin.lista_usuarios'))
    
    return render_template('admin_usuario_form.html')

@bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    u = db.session.get(Usuario, id)
    if not u:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.lista_usuarios'))
    
    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', ''))
        cargo = request.form.get('cargo', 'Usuário')
        senha = request.form.get('senha', '')
        
        if not nome:
            flash('Nome é obrigatório.', 'danger')
            return render_template('admin_usuario_form.html', usuario=u)
        
        antes = {'nome': u.nome, 'cargo': u.cargo}
        
        u.nome = nome
        u.cargo = cargo
        if senha:
            if len(senha) < 8:
                flash('Senha deve ter no mínimo 8 caracteres.', 'danger')
                return render_template('admin_usuario_form.html', usuario=u)
            u.set_senha(senha)
        
        db.session.commit()
        
        audit_log(current_user, 'UPDATE', 'Usuario', u.id,
                  antes, {'nome': u.nome, 'cargo': u.cargo}, request)
        
        flash('Usuário atualizado!', 'success')
        return redirect(url_for('admin.lista_usuarios'))
    
    return render_template('admin_usuario_form.html', usuario=u)

@bp.route('/usuarios/<int:id>/ativar', methods=['POST'])
@login_required
@admin_required
def ativar_usuario(id):
    u = db.session.get(Usuario, id)
    if u:
        antes = {'ativo': u.ativo}
        u.ativo = not u.ativo
        db.session.commit()
        
        from app.utils.audit import audit_log
        audit_log(current_user, 'TOGGLE_ATIVO', 'Usuario', u.id,
                  antes, {'ativo': u.ativo}, request)
    
    return redirect(url_for('admin.lista_usuarios'))

# API para auditoria
@bp.route('/auditoria')
@login_required
@admin_required
def auditoria():
    from app.models import AuditLog
    page = request.args.get('page', 1, type=int)
    acao = request.args.get('acao', '')
    entidade = request.args.get('entidade', '')
    usuario_id = request.args.get('usuario_id', type=int)
    
    query = AuditLog.query
    if acao:
        query = query.filter_by(acao=acao)
    if entidade:
        query = query.filter_by(entidade=entidade)
    if usuario_id:
        query = query.filter_by(usuario_id=usuario_id)
    
    query = query.order_by(AuditLog.criado_em.desc())
    logs = query.paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin_auditoria.html', logs=logs,
                           acao=acao, entidade=entidade, usuario_id=usuario_id)