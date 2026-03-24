from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.cliente import Cliente
from app.extensions import db
from app.decorators.auth_decorators import perfil_required

clientes_bp = Blueprint('clientes', __name__)

# LISTAR CLIENTES
@clientes_bp.route('/')
@perfil_required("admin")
def listar():
    clientes = Cliente.query.all()
    return render_template('clientes/listar.html', clientes=clientes)


# CRIAR CLIENTE
@clientes_bp.route('/novo', methods=['GET', 'POST'])
@perfil_required("admin")
def novo():

    if request.method == 'POST':
        nome_empresa = request.form.get('nome_empresa')
        responsavel = request.form.get('responsavel')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')

        novo_cliente = Cliente(
            nome_empresa=nome_empresa,
            responsavel=responsavel,
            telefone=telefone,
            email=email,
            cidade=cidade,
            estado=estado,
            status=True
        )

        db.session.add(novo_cliente)
        db.session.commit()

        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes.listar'))

    return render_template('clientes/novo.html')


# EDITAR CLIENTE
@clientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@perfil_required("admin")
def editar(id):

    cliente = Cliente.query.get_or_404(id)

    if request.method == 'POST':
        cliente.nome_empresa = request.form.get('nome_empresa')
        cliente.responsavel = request.form.get('responsavel')
        cliente.telefone = request.form.get('telefone')
        cliente.email = request.form.get('email')
        cliente.cidade = request.form.get('cidade')
        cliente.estado = request.form.get('estado')

        db.session.commit()

        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clientes.listar'))

    return render_template('clientes/editar.html', cliente=cliente)


# EXCLUIR CLIENTE
@clientes_bp.route('/excluir/<int:id>', methods=['POST'])
@perfil_required("admin")
def excluir(id):

    cliente = Cliente.query.get_or_404(id)

    db.session.delete(cliente)
    db.session.commit()

    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('clientes.listar'))