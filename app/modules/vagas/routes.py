from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.vaga import Vaga
from app.extensions import db
from app.services.cloudinary_service import CloudinaryService
from datetime import datetime

vagas_bp = Blueprint('vagas', __name__)

# LISTAR VAGAS
@vagas_bp.route('/')
@login_required
def listar():
    vagas = Vaga.query.order_by(Vaga.data_cadastro.desc()).all()
    return render_template('vagas/listar.html', vagas=vagas)


# NOVA VAGA
@vagas_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            dias_disponibilidade = request.form.getlist('disponibilidade[]')

            # Upload documentos para Cloudinary
            arquivos = {
                'rg': CloudinaryService.upload_image(request.files.get('rg'), folder="vagas/documentos"),
                'cpf_doc': CloudinaryService.upload_image(request.files.get('cpf_doc'), folder="vagas/documentos"),
                'titulo_eleitor': CloudinaryService.upload_image(request.files.get('titulo_eleitor'), folder="vagas/documentos"),
                'ctps': CloudinaryService.upload_image(request.files.get('ctps'), folder="vagas/documentos")
            }

            nova_vaga = Vaga(
                dados_pessoais={
                    'nome_completo': request.form['nome_completo'],
                    'data_nascimento': request.form['data_nascimento'],
                    'cpf': request.form['cpf'],
                    'estado_civil': request.form.get('estado_civil', ''),
                    'dependentes': request.form.get('dependentes', '')
                },
                dados_contato={
                    'telefone': request.form['telefone'],
                    'email': request.form['email'],
                    'cep': request.form.get('cep', ''),
                    'cidade': request.form.get('cidade', ''),
                    'estado': request.form.get('estado', '')
                },
                dados_profissionais={
                    'area_atuacao': request.form['area_atuacao'],
                    'tipo_interesse': request.form.get('tipo_interesse', ''),
                    'disponibilidade': ', '.join(dias_disponibilidade),
                    'experiencia': request.form['experiencia']
                },
                dados_bancarios={
                    'banco': request.form.get('banco', ''),
                    'agencia': request.form.get('agencia', ''),
                    'conta': request.form.get('conta', ''),
                    'pix': request.form.get('pix', '')
                },
                arquivos=arquivos
            )

            db.session.add(nova_vaga)
            db.session.commit()

            flash('Candidatura cadastrada com sucesso!', 'success')
            return redirect(url_for('vagas.listar'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar candidatura: {str(e)}', 'danger')

    return render_template('vagas/novo.html')


# EDITAR VAGA
@vagas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):

    vaga = Vaga.query.get_or_404(id)

    if request.method == 'POST':
        try:

            dias_disponibilidade = request.form.getlist('disponibilidade[]')

            # Atualizar dados pessoais
            vaga.dados_pessoais = {
                'nome_completo': request.form['nome_completo'],
                'data_nascimento': request.form['data_nascimento'],
                'cpf': request.form['cpf'],
                'estado_civil': request.form.get('estado_civil', ''),
                'dependentes': request.form.get('dependentes', '')
            }

            # Atualizar contato
            vaga.dados_contato = {
                'telefone': request.form['telefone'],
                'email': request.form['email'],
                'cep': request.form.get('cep', ''),
                'cidade': request.form.get('cidade', ''),
                'estado': request.form.get('estado', '')
            }

            # Atualizar dados profissionais
            vaga.dados_profissionais = {
                'area_atuacao': request.form['area_atuacao'],
                'tipo_interesse': request.form.get('tipo_interesse', ''),
                'disponibilidade': ', '.join(dias_disponibilidade),
                'experiencia': request.form['experiencia']
            }

            # Atualizar dados bancários
            vaga.dados_bancarios = {
                'banco': request.form.get('banco', ''),
                'agencia': request.form.get('agencia', ''),
                'conta': request.form.get('conta', ''),
                'pix': request.form.get('pix', '')
            }

            # Atualizar documentos se enviados
            arquivos = vaga.arquivos or {}

            if request.files.get('rg'):
                arquivos['rg'] = CloudinaryService.upload_image(request.files.get('rg'), folder="vagas/documentos")

            if request.files.get('cpf_doc'):
                arquivos['cpf_doc'] = CloudinaryService.upload_image(request.files.get('cpf_doc'), folder="vagas/documentos")

            if request.files.get('titulo_eleitor'):
                arquivos['titulo_eleitor'] = CloudinaryService.upload_image(request.files.get('titulo_eleitor'), folder="vagas/documentos")

            if request.files.get('ctps'):
                arquivos['ctps'] = CloudinaryService.upload_image(request.files.get('ctps'), folder="vagas/documentos")

            vaga.arquivos = arquivos

            db.session.commit()

            flash('Candidatura atualizada com sucesso!', 'success')
            return redirect(url_for('vagas.listar'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar candidatura: {str(e)}', 'danger')

    return render_template('vagas/editar.html', vaga=vaga)


# EXCLUIR VAGA
@vagas_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):

    vaga = Vaga.query.get_or_404(id)

    try:
        db.session.delete(vaga)
        db.session.commit()

        flash('Candidatura excluída com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir candidatura: {str(e)}', 'danger')

    return redirect(url_for('vagas.listar'))