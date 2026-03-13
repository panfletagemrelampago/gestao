"""
Blueprint do módulo de auditorias de campo.
Gerencia o registro de auditorias, turnos de campo e geração de relatórios.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.auditoria import Auditoria
from app.models.turno import Turno
from app.models.area_atuacao import AreaAtuacao
from app.models.foto_auditoria import FotoAuditoria
from app.models.equipe import Equipe
from app.models.veiculo import Veiculo
from app.models.cliente import Cliente
from app.services.cloudinary_service import CloudinaryService
from app.extensions import db

auditorias_bp = Blueprint('auditorias', __name__)


@auditorias_bp.route('/')
@login_required
def listar():
    """Lista todas as auditorias (fotos registradas), com filtro por perfil."""
    if current_user.tipo_usuario == 'admin':
        auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).all()
    elif current_user.tipo_usuario == 'equipe':
        auditorias = Auditoria.query.filter_by(user_id=current_user.id).order_by(
            Auditoria.data_hora.desc()
        ).all()
    else:
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if cliente:
            acao_ids = [a.id for a in AcaoPromocional.query.filter_by(cliente_id=cliente.id).all()]
            auditorias = Auditoria.query.filter(
                Auditoria.acao_id.in_(acao_ids)
            ).order_by(Auditoria.data_hora.desc()).all()
        else:
            auditorias = []

    return render_template('auditorias/listar.html', auditorias=auditorias)


@auditorias_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():
    """Registra uma nova auditoria (foto geolocalizada) via formulário web."""
    acoes_ativas = AcaoPromocional.query.filter(
        AcaoPromocional.status.in_(['Planejada', 'Em Andamento'])
    ).all()

    if request.method == 'POST':
        acao_id = request.form.get('acao_id')
        descricao = request.form.get('descricao')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        foto = request.files.get('foto')

        if not all([acao_id, lat, lon, foto]):
            flash('Preencha todos os campos obrigatórios e tire uma foto.', 'warning')
            return redirect(url_for('auditorias.registrar'))

        foto_url = CloudinaryService.upload_image(foto)
        if not foto_url:
            flash('Erro ao enviar foto para o servidor de imagens.', 'danger')
            return redirect(url_for('auditorias.registrar'))

        nova_auditoria = Auditoria(
            acao_id=acao_id,
            user_id=current_user.id,
            descricao=descricao,
            foto_url=foto_url,
            latitude=float(lat),
            longitude=float(lon),
            data_hora=datetime.utcnow()
        )
        db.session.add(nova_auditoria)
        db.session.commit()

        flash('Auditoria registrada com sucesso!', 'success')
        return redirect(url_for('auditorias.listar'))

    return render_template('auditorias/registrar.html', acoes=acoes_ativas)


@auditorias_bp.route('/turnos/<int:acao_id>')
@login_required
def turnos(acao_id):
    """Exibe e gerencia os turnos de campo de uma ação específica."""
    acao = AcaoPromocional.query.get_or_404(acao_id)

    # Verificar permissão de cliente
    if current_user.tipo_usuario == 'cliente':
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente or acao.cliente_id != cliente.id:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('auditorias.listar'))

    equipes = Equipe.query.filter_by(status=True).all()
    veiculos = Veiculo.query.filter_by(status=True).all()

    return render_template(
        'auditorias/turnos.html',
        acao=acao,
        equipes=equipes,
        veiculos=veiculos
    )


@auditorias_bp.route('/relatorio/<int:acao_id>')
@login_required
def relatorio(acao_id):
    """Gera e exibe o relatório completo de auditoria de uma ação."""
    acao = AcaoPromocional.query.get_or_404(acao_id)

    # Verificar permissão de cliente
    if current_user.tipo_usuario == 'cliente':
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente or acao.cliente_id != cliente.id:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('auditorias.listar'))

    turnos = Turno.query.filter_by(acao_id=acao_id).order_by(Turno.inicio.asc()).all()
    areas = AreaAtuacao.query.filter_by(acao_id=acao_id).all()
    fotos = FotoAuditoria.query.join(Turno).filter(
        Turno.acao_id == acao_id
    ).order_by(FotoAuditoria.data_hora.asc()).all()

    return render_template(
        'auditorias/relatorio.html',
        acao=acao,
        turnos=turnos,
        areas=areas,
        fotos=fotos,
        agora=datetime.utcnow()
    )
