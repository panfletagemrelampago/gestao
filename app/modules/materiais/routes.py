from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.material import Material
from app.extensions import db
from app.services.cloudinary_service import CloudinaryService
from datetime import datetime

materiais_bp = Blueprint('materiais', __name__)

@materiais_bp.route('/')
@login_required
def listar():
    materiais = Material.query.order_by(Material.data_cadastro.desc()).all()
    return render_template('materiais/listar.html', materiais=materiais)

@materiais_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            documento_url = CloudinaryService.upload_image(
                request.files.get('documento'),
                folder="materiais/documentos"
            )

            imagem_url = CloudinaryService.upload_image(
                request.files.get('imagem'),
                folder="materiais/fotos"
            )

            novo_material = Material(
                empresa=request.form['empresa'],
                quantidade=request.form.get('quantidade', type=int),
                data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                data_termino=datetime.strptime(request.form['data_termino'], '%Y-%m-%d').date(),
                nome_campanha=request.form['nome_campanha'],
                responsavel=request.form['responsavel'],
                documento_url=documento_url,
                imagem_url=imagem_url
            )

            db.session.add(novo_material)
            db.session.commit()

            flash('Material cadastrado com sucesso!', 'success')
            return redirect(url_for('materiais.listar'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar material: {str(e)}', 'danger')

    return render_template('materiais/novo.html')

@materiais_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    material = Material.query.get_or_404(id)

    if request.method == 'POST':
        try:
            material.empresa = request.form['empresa']
            material.quantidade = request.form.get('quantidade', type=int)

            material.data_inicio = datetime.strptime(
                request.form['data_inicio'],
                '%Y-%m-%d'
            ).date()

            material.data_termino = datetime.strptime(
                request.form['data_termino'],
                '%Y-%m-%d'
            ).date()

            material.nome_campanha = request.form['nome_campanha']
            material.responsavel = request.form['responsavel']

            documento = request.files.get('documento')
            if documento and documento.filename != '':
                material.documento_url = CloudinaryService.upload_image(
                    documento,
                    folder="materiais/documentos"
                )

            imagem = request.files.get('imagem')
            if imagem and imagem.filename != '':
                material.imagem_url = CloudinaryService.upload_image(
                    imagem,
                    folder="materiais/fotos"
                )

            db.session.commit()

            flash('Material atualizado com sucesso!', 'success')
            return redirect(url_for('materiais.listar'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar material: {str(e)}', 'danger')

    return render_template('materiais/editar.html', material=material)

@materiais_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    material = Material.query.get_or_404(id)

    try:
        db.session.delete(material)
        db.session.commit()
        flash('Material excluído com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir material: {str(e)}', 'danger')

    return redirect(url_for('materiais.listar'))