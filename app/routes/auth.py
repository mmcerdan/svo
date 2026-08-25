from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter
from app.models import Usuario
from app.utils.security import sanitize_input
from app.forms import LoginForm
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if request.method == 'POST':
        usuario = sanitize_input(request.form.get('usuario', ''))
        senha = request.form.get('senha', '')
        
        if not usuario or not senha:
            flash('Preencha usuário e senha.', 'danger')
            return render_template('login.html', form=form)
        
        user = Usuario.query.filter_by(usuario=usuario).first()
        
        if user and user.check_senha(senha) and user.ativo:
            login_user(user)
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            
            from app.utils.audit import audit_log
            audit_log(user, 'LOGIN', 'Usuario', user.id)
            
            flash(f'Bem-vindo, {user.nome}!', 'success')
            return redirect(url_for('main.index'))
        
        from app.utils.audit import audit_log
        audit_log(None, 'LOGIN_FAILED', 'Usuario', None, 
                  {'usuario_tentado': usuario}, None)
        
        flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id if current_user.is_authenticated else None
    user_nome = current_user.nome if current_user.is_authenticated else None
    logout_user()
    flash('Sessão encerrada.', 'info')
    
    from app.utils.audit import audit_log
    audit_log(None, 'LOGOUT', 'Usuario', user_id)
    
    return redirect(url_for('auth.login'))