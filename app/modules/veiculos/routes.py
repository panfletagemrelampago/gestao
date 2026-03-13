from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.veiculo import Veiculo
from app.models.equipe import Equipe
from app.extensions import db

veiculos_bp = Blueprint('veiculos', __name__)


# LISTAR VEICULOS
@veiculos_bp.route('/')
@login_required
def listar():

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.dashboard'))

    veiculos = Veiculo.query.all()

    return render_template('veiculos/listar.html', veiculos=veiculos)



# NOVO VEICULO
@veiculos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('veiculos.listar'))

    equipes = Equipe.query.all()

    if request.method == 'POST':

        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        placa = request.form.get('placa')
        cor = request.form.get('cor')
        motorista_id = request.form.get('motorista_id')

        novo_veiculo = Veiculo(
            marca=marca,
            modelo=modelo,
            placa=placa,
            cor=cor,
            motorista_id=motorista_id if motorista_id else None,
            status=True
        )

        db.session.add(novo_veiculo)
        db.session.commit()

        flash('Veículo cadastrado com sucesso!', 'success')

        return redirect(url_for('veiculos.listar'))

    return render_template('veiculos/novo.html', equipes=equipes)



# EDITAR VEICULO
@veiculos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('veiculos.listar'))

    veiculo = Veiculo.query.get_or_404(id)

    equipes = Equipe.query.all()

    if request.method == 'POST':

        veiculo.marca = request.form.get('marca')
        veiculo.modelo = request.form.get('modelo')
        veiculo.placa = request.form.get('placa')
        veiculo.cor = request.form.get('cor')

        motorista_id = request.form.get('motorista_id')
        veiculo.motorista_id = motorista_id if motorista_id else None

        db.session.commit()

        flash('Veículo atualizado com sucesso!', 'success')

        return redirect(url_for('veiculos.listar'))

    return render_template('veiculos/editar.html', veiculo=veiculo, equipes=equipes)



# EXCLUIR VEICULO
@veiculos_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('veiculos.listar'))

    veiculo = Veiculo.query.get_or_404(id)

    try:

        db.session.delete(veiculo)
        db.session.commit()

        flash('Veículo excluído com sucesso!', 'success')

    except Exception as e:

        db.session.rollback()
        flash(f'Erro ao excluir veículo: {str(e)}', 'danger')

    return redirect(url_for('veiculos.listar'))