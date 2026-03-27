from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.veiculo import Veiculo
from app.models.equipe import Equipe
from app.extensions import db
from app.decorators.auth_decorators import perfil_required

veiculos_bp = Blueprint('veiculos', __name__)


# LISTAR VEICULOS
@veiculos_bp.route('/')
@perfil_required("admin")
def listar():
    query = Veiculo.query
    
    search = request.args.get('search')
    if search:
        query = query.filter(
            (Veiculo.marca.ilike(f'%{search}%')) |
            (Veiculo.modelo.ilike(f'%{search}%')) |
            (Veiculo.placa.ilike(f'%{search}%')) |
            (Veiculo.cor.ilike(f'%{search}%'))
        )
        
    veiculos = query.all()
    return render_template('veiculos/listar.html', veiculos=veiculos)


# NOVO VEICULO
@veiculos_bp.route('/novo', methods=['GET', 'POST'])
@perfil_required("admin")
def novo():

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
@perfil_required("admin")
def editar(id):

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
@perfil_required("admin")
def excluir(id):

    veiculo = Veiculo.query.get_or_404(id)

    try:

        db.session.delete(veiculo)
        db.session.commit()

        flash('Veículo excluído com sucesso!', 'success')

    except Exception as e:

        db.session.rollback()
        flash(f'Erro ao excluir veículo: {str(e)}', 'danger')

    return redirect(url_for('veiculos.listar'))