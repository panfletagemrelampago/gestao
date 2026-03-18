from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.equipe import Equipe
from app.extensions import db
from datetime import datetime

acoes_bp = Blueprint('acoes', __name__)


@acoes_bp.route('/')
@login_required
def listar():
    if current_user.tipo_usuario == 'admin':
        acoes = AcaoPromocional.query.all()
    elif current_user.tipo_usuario == 'equipe':
        acoes = AcaoPromocional.query.filter_by(lider_equipe_id=current_user.id).all()
    else:
        # Cliente vê apenas suas ações
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if cliente:
            acoes = AcaoPromocional.query.filter_by(cliente_id=cliente.id).all()
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

    # Verificação básica de permissão
    if current_user.tipo_usuario not in ['admin', 'equipe']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('acoes.listar'))

    acao.status = novo_status
    db.session.commit()

    flash(f'Status da ação {acao.local_alvo} atualizado para {novo_status}.', 'info')
    return redirect(url_for('acoes.listar'))
