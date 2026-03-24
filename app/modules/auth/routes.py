from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


def redirect_by_role(user):
    """
    Redireciona o usuário para o dashboard correto conforme seu perfil.

    - funcionario → /funcionario/dashboard
    - cliente     → /cliente/dashboard
    - admin       → /dashboard (dashboard principal)
    """
    if user.tipo_usuario == "funcionario":
        return redirect(url_for("funcionario.dashboard"))
    elif user.tipo_usuario == "cliente":
        return redirect(url_for("cliente.dashboard"))
    else:
        # admin e outros perfis vão para o dashboard principal
        return redirect(url_for("main.dashboard"))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Login inválido. Verifique seu e-mail e senha.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.ativo:
            flash('Sua conta está inativa. Entre em contato com o administrador.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)

        # Respeita o parâmetro ?next= se existir, senão redireciona por perfil
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect_by_role(user)

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
