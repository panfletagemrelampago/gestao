from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.cliente import Cliente
from app.decorators.auth_decorators import perfil_required

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuarios_bp.route('/')
@perfil_required('admin')
def listar():
    query = User.query.filter_by(ativo=True)
    
    search = request.args.get('search')
    if search:
        query = query.filter(
            (User.nome_exibicao.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.tipo_usuario.ilike(f'%{search}%'))
        )
        
    usuarios = query.all()
    return render_template('usuarios/listar.html', usuarios=usuarios)

@usuarios_bp.route('/novo', methods=['GET', 'POST'])
@perfil_required('admin')
def novo():
    clientes = Cliente.query.all()
    
    if request.method == 'POST':
        nome = request.form.get('nome_exibicao')
        email = request.form.get('email')
        tipo = request.form.get('tipo_usuario')
        senha = request.form.get('senha')
        cliente_id = request.form.get('cliente_id') if tipo == 'cliente' else None
        
        # Validações
        if not all([nome, email, tipo, senha]):
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'warning')
            return redirect(url_for('usuarios.novo'))
            
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado no sistema.', 'danger')
            return redirect(url_for('usuarios.novo'))
            
        try:
            novo_usuario = User(
                nome_exibicao=nome,
                email=email,
                tipo_usuario=tipo,
                cliente_id=cliente_id
            )
            novo_usuario.set_password(senha)
            
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('usuarios.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')
    
    return render_template('usuarios/form.html', 
                         usuario=None, 
                         clientes=clientes, 
                         titulo='Novo Usuário')

@usuarios_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@perfil_required('admin')
def editar(id):
    usuario = User.query.get_or_404(id)
    clientes = Cliente.query.all()
    
    if request.method == 'POST':
        nome = request.form.get('nome_exibicao')
        email = request.form.get('email')
        tipo = request.form.get('tipo_usuario')
        senha = request.form.get('senha')  # Opcional no editar
        cliente_id = request.form.get('cliente_id') if tipo == 'cliente' else None
        
        # Validações
        if not all([nome, email, tipo]):
            flash('Nome, e-mail e tipo são obrigatórios.', 'warning')
            return redirect(url_for('usuarios.editar', id=id))
            
        # Verifica se email já existe (exceto o próprio usuário)
        existente = User.query.filter_by(email=email).first()
        if existente and existente.id != id:
            flash('E-mail já cadastrado para outro usuário.', 'danger')
            return redirect(url_for('usuarios.editar', id=id))
            
        try:
            usuario.nome_exibicao = nome
            usuario.email = email
            usuario.tipo_usuario = tipo
            usuario.cliente_id = cliente_id
            
            if senha:  # Só atualiza senha se foi preenchida
                usuario.set_password(senha)
                
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('usuarios.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
    
    return render_template('usuarios/form.html', 
                         usuario=usuario, 
                         clientes=clientes, 
                         titulo='Editar Usuário')

@usuarios_bp.route('/<int:id>/excluir', methods=['POST'])
@perfil_required('admin')
def excluir(id):
    usuario = User.query.get_or_404(id)
    
    # Impedir que o admin exclua a si mesmo
    if usuario.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('usuarios.listar'))
    
    try:
        usuario.soft_delete() # Chama o método soft_delete do modelo User
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')
        
    return redirect(url_for('usuarios.listar'))
