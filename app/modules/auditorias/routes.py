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


# =============================
# LISTAR AUDITORIAS
# =============================
@auditorias_bp.route('/')
@login_required
def listar():
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


# =============================
# REGISTRAR FOTO (COM TURNO)
# =============================
@auditorias_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():
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
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            flash('Erro ao capturar localização.', 'danger')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        # 🔥 TURNO ATIVO (GARANTIR EXISTÊNCIA)
        turno_ativo = Turno.query.filter_by(
            acao_id=acao_id,
            status='ativo'
        ).first()

        if not turno_ativo:
            # Criar automaticamente se não existir
            turno_ativo = Turno(acao_id=acao_id, status='ativo')
            db.session.add(turno_ativo)
            db.session.commit()

        foto_url = CloudinaryService.upload_image(foto)
        if not foto_url:
            flash('Erro ao enviar imagem.', 'danger')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        try:
            nova_auditoria = Auditoria(
                acao_id=acao_id,
                user_id=current_user.id,
                descricao=descricao,
                foto_url=foto_url,
                latitude=lat,
                longitude=lon,
                data_hora=datetime.utcnow()
            )
            db.session.add(nova_auditoria)

            nova_foto = FotoAuditoria(
                url=foto_url,
                latitude=lat,
                longitude=lon,
                descricao=descricao,
                data_hora=datetime.utcnow(),
                turno_id=turno_ativo.id
            )
            db.session.add(nova_foto)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        flash('Auditoria registrada!', 'success')
        return redirect(url_for('auditorias.listar'))

    return render_template('auditorias/registrar.html', acoes=acoes_ativas)


# =============================
# TELA DE TURNOS
# =============================
@auditorias_bp.route('/turnos/<int:acao_id>')
@login_required
def turnos(acao_id):
    acao = AcaoPromocional.query.get_or_404(acao_id)

    if current_user.tipo_usuario == 'cliente':
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente or acao.cliente_id != cliente.id:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('auditorias.listar'))

    equipes = Equipe.query.filter_by(status=True).all()
    veiculos = Veiculo.query.filter_by(status=True).all()
    turnos = Turno.query.filter_by(acao_id=acao_id).order_by(Turno.inicio.desc()).all()

    return render_template(
        'auditorias/turnos.html',
        acao=acao,
        equipes=equipes,
        veiculos=veiculos,
        turnos=turnos
    )


# =============================
# RELATÓRIO
# =============================
@auditorias_bp.route('/relatorio/<int:acao_id>')
@login_required
def relatorio(acao_id):
    acao = AcaoPromocional.query.get_or_404(acao_id)

    turnos = Turno.query.filter_by(acao_id=acao_id).all()
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


# =============================
# 🔥 TURNOS (CRUD COMPLETO)
# =============================

@auditorias_bp.route('/turno/iniciar/<int:acao_id>', methods=['POST'])
@login_required
def iniciar_turno(acao_id):
    # Encerrar turnos anteriores antes de iniciar um novo
    Turno.query.filter_by(acao_id=acao_id, status='ativo').update({'status': 'encerrado', 'fim': datetime.utcnow()})

    turno = Turno(
        acao_id=acao_id,
        equipe_id=request.form.get('equipe_id'),
        veiculo_id=request.form.get('veiculo_id'),
        status='ativo'
    )

    db.session.add(turno)
    db.session.commit()

    flash('Turno iniciado!', 'success')
    return redirect(url_for('auditorias.turnos', acao_id=acao_id))





@auditorias_bp.route('/turno/encerrar/<int:turno_id>')
@login_required
def encerrar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)

    turno.status = 'encerrado'
    turno.fim = datetime.utcnow()

    db.session.commit()

    flash('Turno encerrado.', 'success')
    return redirect(url_for('auditorias.turnos', acao_id=turno.acao_id))


@auditorias_bp.route('/turno/cancelar/<int:turno_id>')
@login_required
def cancelar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)

    db.session.delete(turno)
    db.session.commit()

    flash('Turno cancelado.', 'danger')
    return redirect(url_for('auditorias.turnos', acao_id=turno.acao_id))


@auditorias_bp.route('/turno/editar/<int:turno_id>', methods=['POST'])
@login_required
def editar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)

    turno.equipe_id = request.form.get('equipe_id')
    turno.veiculo_id = request.form.get('veiculo_id')
    turno.observacoes = request.form.get('observacoes')

    db.session.commit()

    flash('Turno atualizado.', 'success')
    return redirect(url_for('auditorias.turnos', acao_id=turno.acao_id))


@auditorias_bp.route('/turno/excluir/<int:turno_id>')
@login_required
def excluir_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)

    db.session.delete(turno)
    db.session.commit()

    flash('Turno excluído.', 'danger')
    return redirect(url_for('auditorias.turnos', acao_id=turno.acao_id))


# =============================
# 🔥 EXCLUIR AUDITORIA
# =============================
@auditorias_bp.route('/excluir/<int:auditoria_id>', methods=['POST'])
@login_required
def excluir_auditoria(auditoria_id):
    auditoria = Auditoria.query.get_or_404(auditoria_id)

    try:
        db.session.delete(auditoria)
        db.session.commit()
        flash('Auditoria excluída com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir auditoria.', 'danger')

    return redirect(url_for('auditorias.listar'))
