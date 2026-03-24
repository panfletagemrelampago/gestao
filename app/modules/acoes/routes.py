from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.equipe import Equipe
from app.models.turno import Turno
from app.models.foto_auditoria import FotoAuditoria
from app.extensions import db
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_acoes_por_perfil
from datetime import datetime

acoes_bp = Blueprint('acoes', __name__)


@acoes_bp.route('/')
@perfil_required("admin", "funcionario", "cliente")
def listar():
    """
    Lista ações conforme o perfil do usuário:
    - admin: todas as ações
    - funcionario: ações em que é líder de equipe
    - cliente: ações vinculadas ao seu cliente_id
    """
    acoes = get_acoes_por_perfil()
    return render_template('acoes/listar.html', acoes=acoes)


@acoes_bp.route('/nova', methods=['GET', 'POST'])
@perfil_required("admin")
def nova():

    clientes = Cliente.query.all()
    equipes = Equipe.query.all()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        nome_campanha = request.form.get('nome_campanha', '').strip() or None
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
            nome_campanha=nome_campanha,
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
@perfil_required("admin", "funcionario")
def atualizar_status(id):
    acao = AcaoPromocional.query.get_or_404(id)
    novo_status = request.form.get('status')

    acao.status = novo_status
    db.session.commit()

    flash(
        f'Status da ação {acao.nome_exibicao} atualizado para {novo_status}.',
        'info'
    )

    return redirect(url_for('acoes.listar'))


@acoes_bp.route('/excluir/<int:id>', methods=['POST'])
@perfil_required("admin")
def excluir(id):

    acao = AcaoPromocional.query.get_or_404(id)

    try:
        # 1. Deletar auditorias vinculadas à ação
        for auditoria in acao.auditorias:
            db.session.delete(auditoria)

        # 2. Buscar turnos da ação para deletar fotos vinculadas
        turnos = Turno.query.filter_by(acao_id=id).all()
        for turno in turnos:
            # 2.1 Deletar fotos vinculadas ao turno (FotoAuditoria)
            for foto in turno.fotos:
                db.session.delete(foto)
            
            # 2.2 Deletar o turno
            db.session.delete(turno)

        # 3. Deletar a ação
        db.session.delete(acao)
        db.session.commit()

        flash('Ação excluída com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        print("Erro ao excluir ação:", e)
        flash('Erro ao excluir ação.', 'danger')

    return redirect(url_for('acoes.listar'))
