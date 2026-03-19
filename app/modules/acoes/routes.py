from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.equipe import Equipe
from app.models.turno import Turno
from app.models.foto_auditoria import FotoAuditoria  # 🔥 NOVO
from app.extensions import db
from datetime import datetime

acoes_bp = Blueprint('acoes', __name__)


@acoes_bp.route('/')
@login_required
def listar():
    if current_user.tipo_usuario == 'admin':
        acoes = AcaoPromocional.query.all()

    elif current_user.tipo_usuario == 'equipe':
        acoes = AcaoPromocional.query.filter_by(
            lider_equipe_id=current_user.id
        ).all()

    else:
        cliente = Cliente.query.filter_by(email=current_user.email).first()

        if cliente:
            acoes = AcaoPromocional.query.filter_by(
                cliente_id=cliente.id
            ).all()
        else:
            acoes = []

    return render_template('acoes/listar.html', acoes=acoes)


@acoes_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('acoes.listar'))

    clientes = Cliente.query.all()
    equipes = Equipe.query.all()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        local_alvo = request.form.get('local_alvo')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        tipo_servico = request.form.get('tipo_servico')
        data_str = request.form.get('data')
        turno = request.form.get('turno')
        lider_id = request.form.get('lider_id')
        descricao = request.form.get('descricao')

        lider_id = int(lider_id) if lider_id else None

        nova_acao = AcaoPromocional(
            cliente_id=cliente_id,
            local_alvo=local_alvo,
            bairro=bairro,
            cidade=cidade,
            tipo_servico=tipo_servico,
            data=datetime.strptime(data_str, '%Y-%m-%d').date(),
            turno=turno,
            lider_equipe_id=lider_id,
            descricao=descricao,
            status='Planejada'
        )

        db.session.add(nova_acao)
        db.session.commit()

        flash('Ação promocional criada com sucesso!', 'success')
        return redirect(url_for('acoes.listar'))

    return render_template('acoes/nova.html', clientes=clientes, equipes=equipes)


@acoes_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def atualizar_status(id):
    acao = AcaoPromocional.query.get_or_404(id)
    novo_status = request.form.get('status')

    if current_user.tipo_usuario not in ['admin', 'equipe']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('acoes.listar'))

    acao.status = novo_status
    db.session.commit()

    flash(
        f'Status da ação {acao.local_alvo} atualizado para {novo_status}.',
        'info'
    )

    return redirect(url_for('acoes.listar'))


@acoes_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):

    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('acoes.listar'))

    acao = AcaoPromocional.query.get_or_404(id)

    try:
        # 🔥 1. Buscar turnos da ação
        turnos = Turno.query.filter_by(acao_id=id).all()

        for turno in turnos:
            # 🔥 2. Deletar fotos do turno
            fotos = FotoAuditoria.query.filter_by(turno_id=turno.id).all()
            for foto in fotos:
                db.session.delete(foto)

            # 🔥 3. Deletar turno
            db.session.delete(turno)

        # 🔥 4. Deletar ação
        db.session.delete(acao)

        db.session.commit()

        flash('Ação excluída com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        print("Erro ao excluir ação:", e)
        flash('Erro ao excluir ação.', 'danger')

    return redirect(url_for('acoes.listar'))