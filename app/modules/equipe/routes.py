from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.equipe import Equipe
from app.models.acao_promocional import AcaoPromocional
from app.extensions import db

equipe_bp = Blueprint('equipe', __name__)


# LISTAR MEMBROS
@equipe_bp.route('/')
@login_required
def listar():

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.dashboard'))

    equipes = Equipe.query.all()

    return render_template('equipe/listar.html', equipes=equipes)


# NOVO MEMBRO
@equipe_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('equipe.listar'))

    if request.method == 'POST':

        nome = request.form.get('nome')
        cargo = request.form.get('cargo')
        telefone = request.form.get('telefone')

        if not nome:
            flash('Nome é obrigatório.', 'warning')
            return redirect(url_for('equipe.novo'))

        novo_membro = Equipe(
            nome=nome,
            cargo=cargo,
            telefone=telefone,
            status=True
        )

        db.session.add(novo_membro)
        db.session.commit()

        flash('Membro cadastrado com sucesso!', 'success')

        return redirect(url_for('equipe.listar'))

    return render_template('equipe/novo.html')


# EDITAR MEMBRO
@equipe_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('equipe.listar'))

    membro = Equipe.query.get_or_404(id)

    if request.method == 'POST':

        membro.nome = request.form.get('nome')
        membro.cargo = request.form.get('cargo')
        membro.telefone = request.form.get('telefone')

        db.session.commit()

        flash('Membro atualizado com sucesso!', 'success')

        return redirect(url_for('equipe.listar'))

    return render_template('equipe/editar.html', membro=membro)


# EXCLUIR MEMBRO (COM DESVINCULAÇÃO DAS AÇÕES)
@equipe_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('equipe.listar'))

    membro = Equipe.query.get_or_404(id)

    try:
        # 🔥 1. Buscar ações vinculadas
        acoes = AcaoPromocional.query.filter_by(lider_equipe_id=id).all()

        # 🔥 2. Desvincular
        for acao in acoes:
            acao.lider_equipe_id = None

        # 🗑 3. Excluir membro
        db.session.delete(membro)
        db.session.commit()

        flash('Membro excluído e ações desvinculadas com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        print("Erro ao excluir membro:", e)  # 👈 debug útil
        flash('Erro ao excluir membro.', 'danger')

    return redirect(url_for('equipe.listar'))