"""
Blueprint do módulo de auditorias de campo.
Gerencia o registro de fotos de campo, turnos e geração de relatórios.

REFATORAÇÃO (Passos 1 e 3):
- Removida escrita dupla em Auditoria + FotoAuditoria; agora apenas FotoAuditoria
  é persistida (fonte de verdade única).
- Rota listar() migrada para FotoAuditoria com filtros equivalentes.
- Rota excluir_auditoria() mantida por compatibilidade de URL, mas opera sobre
  FotoAuditoria.
- get_local_now() e to_local_tz() mantidos APENAS para exibição em templates.
- Heurística de veículo do líder removida da rota turnos(); delegada a
  Veiculo.buscar_para_lider() (Passo 3).
- data_hora persistida em UTC via _utcnow().
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.turno import Turno
from app.models.area_atuacao import AreaAtuacao
from app.models.foto_auditoria import FotoAuditoria
from app.models.equipe import Equipe
from app.models.veiculo import Veiculo
from app.models.cliente import Cliente
from app.services.cloudinary_service import CloudinaryService
from app.services.turno_service import TurnoService
from app.extensions import db
from app.decorators.auth_decorators import perfil_required

auditorias_bp = Blueprint('auditorias', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE EXIBIÇÃO (conversão de fuso apenas para templates/relatórios)
# ─────────────────────────────────────────────────────────────────────────────

def _utcnow():
    """UTC naive para persistência."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_local_now():
    """Cuiabá (GMT-4) naive — uso exclusivo em exibição."""
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=-4))
    ).replace(tzinfo=None)


def to_local_tz(dt):
    """Converte UTC naive/aware para GMT-4 naive — uso exclusivo em exibição."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=-4))).replace(tzinfo=None)


# ─────────────────────────────────────────────────────────────────────────────
# LISTAR FOTOS DE CAMPO (substitui listagem legada de Auditoria)
# ─────────────────────────────────────────────────────────────────────────────

@auditorias_bp.route('/')
@perfil_required("admin", "funcionario")
def listar():
    """
    Lista fotos de campo conforme o perfil:
    - admin: todas as fotos
    - funcionario: apenas as que ele registrou
    """
    if current_user.tipo_usuario == 'admin':
        fotos = FotoAuditoria.query.order_by(FotoAuditoria.data_hora.desc()).all()
    else:
        fotos = FotoAuditoria.query.filter_by(
            usuario_id=current_user.id
        ).order_by(FotoAuditoria.data_hora.desc()).all()

    return render_template('auditorias/listar.html', auditorias=fotos)


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRAR FOTO (COM TURNO)
# ─────────────────────────────────────────────────────────────────────────────

@auditorias_bp.route('/registrar', methods=['GET', 'POST'])
@perfil_required("admin", "funcionario")
def registrar():
    acoes_ativas = AcaoPromocional.query.filter(
        AcaoPromocional.status.in_(['Planejada', 'Em Andamento'])
    ).order_by(AcaoPromocional.cliente_id, AcaoPromocional.data.desc()).all()

    clientes_acoes = {}
    for acao in acoes_ativas:
        cliente_nome = acao.cliente.nome_empresa if acao.cliente else 'Sem Cliente'
        if cliente_nome not in clientes_acoes:
            clientes_acoes[cliente_nome] = []
        clientes_acoes[cliente_nome].append(acao)

    if request.method == 'POST':
        acao_id = request.form.get('acao_id')
        descricao = request.form.get('descricao')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        foto = request.files.get('foto')

        if not all([acao_id, lat, lon, foto]):
            flash('Preencha todos os campos obrigatórios e tire uma foto.', 'warning')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        acao = AcaoPromocional.query.get(acao_id)
        if not acao:
            flash('Ação não encontrada.', 'danger')
            return redirect(url_for('auditorias.registrar'))

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            flash('Erro ao capturar localização.', 'danger')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        # Garantir turno ativo
        turno_ativo = Turno.query.filter(
            Turno.acao_id == acao_id,
            Turno.status == 'em andamento'
        ).first()

        if not turno_ativo:
            if current_user.tipo_usuario == 'funcionario':
                try:
                    turno_ativo = TurnoService.iniciar_turno(acao_id, current_user)
                except ValueError as e:
                    flash(str(e), 'danger')
                    return redirect(url_for('auditorias.registrar', acao_id=acao_id))
            else:
                flash(
                    'Não há turno em andamento para esta ação. '
                    'Peça ao funcionário para iniciar um turno.',
                    'warning'
                )
                return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        foto_url = CloudinaryService.upload_image(foto)
        if not foto_url:
            flash('Erro ao enviar imagem.', 'danger')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        try:
            nova_foto = FotoAuditoria(
                url=foto_url,
                latitude=lat,
                longitude=lon,
                descricao=descricao,
                data_hora=_utcnow(),          # UTC — padronização Passo 1
                turno_id=turno_ativo.id,
                acao_id=int(acao_id),          # vínculo direto com a ação
                usuario_id=current_user.id,    # OWNERSHIP
                cliente_id=acao.cliente_id     # OWNERSHIP
            )
            db.session.add(nova_foto)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'danger')
            return redirect(url_for('auditorias.registrar', acao_id=acao_id))

        flash('Foto de campo registrada!', 'success')
        return redirect(url_for('auditorias.listar'))

    return render_template(
        'auditorias/registrar.html',
        acoes=acoes_ativas,
        clientes_acoes=clientes_acoes
    )


# ─────────────────────────────────────────────────────────────────────────────
# TELA DE TURNOS
# ─────────────────────────────────────────────────────────────────────────────

@auditorias_bp.route('/turnos/<int:acao_id>')
@perfil_required("admin", "funcionario", "cliente")
def turnos(acao_id):
    from app.utils.security_helpers import get_acao_segura
    acao = get_acao_segura(acao_id)

    if acao.lider_equipe_id and not acao.lider:
        acao.lider = Equipe.query.get(acao.lider_equipe_id)

    equipes = Equipe.query.filter_by(status=True).all()
    veiculos = Veiculo.query.filter_by(status=True).all()
    turnos_lista = Turno.query.filter_by(acao_id=acao_id).order_by(Turno.inicio.desc()).all()

    # Heurística centralizada (Passo 3): única fonte da verdade
    veiculo_lider = Veiculo.buscar_para_lider(acao.lider_equipe_id, acao.lider)

    return render_template(
        'auditorias/turnos.html',
        acao=acao,
        equipes=equipes,
        veiculos=veiculos,
        turnos=turnos_lista,
        veiculo_lider=veiculo_lider
    )


# ─────────────────────────────────────────────────────────────────────────────
# RELATÓRIO
# ─────────────────────────────────────────────────────────────────────────────

@auditorias_bp.route('/relatorio/<int:acao_id>')
@perfil_required("admin", "funcionario", "cliente")
def relatorio(acao_id):
    from app.utils.security_helpers import get_acao_segura
    acao = get_acao_segura(acao_id)
    turnos_acao = Turno.query.filter_by(acao_id=acao_id).all()
    areas = AreaAtuacao.query.filter_by(acao_id=acao_id).all()
    fotos = FotoAuditoria.query.join(Turno).filter(
        Turno.acao_id == acao_id
    ).order_by(FotoAuditoria.data_hora.asc()).all()

    return render_template(
        'auditorias/relatorio.html',
        acao=acao,
        turnos=turnos_acao,
        areas=areas,
        fotos=fotos,
        agora=get_local_now()   # exibição apenas
    )


# ─────────────────────────────────────────────────────────────────────────────
# MÁQUINA DE ESTADOS DOS TURNOS
# ─────────────────────────────────────────────────────────────────────────────

@auditorias_bp.route('/turno/iniciar/<int:acao_id>', methods=['POST'])
@perfil_required("funcionario")
def iniciar_turno(acao_id):
    try:
        TurnoService.iniciar_turno(acao_id, current_user)
        flash('Turno iniciado!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('auditorias.turnos', acao_id=acao_id))


@auditorias_bp.route('/turno/pausar/<int:turno_id>', methods=['POST'])
@perfil_required("funcionario")
def pausar_turno(turno_id):
    try:
        TurnoService.pausar_turno(turno_id, current_user)
        return jsonify({'status': 'sucesso', 'mensagem': 'Turno pausado.'})
    except ValueError as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400


@auditorias_bp.route('/turno/retomar/<int:turno_id>', methods=['POST'])
@perfil_required("funcionario")
def retomar_turno(turno_id):
    try:
        TurnoService.retomar_turno(turno_id, current_user)
        return jsonify({'status': 'sucesso', 'mensagem': 'Turno retomado.'})
    except ValueError as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400


@auditorias_bp.route('/turno/encerrar/<int:turno_id>', methods=['POST'])
@perfil_required("funcionario")
def encerrar_turno(turno_id):
    obs = request.form.get('observacoes')
    try:
        TurnoService.encerrar_turno(turno_id, current_user, obs)
        return jsonify({'status': 'sucesso', 'mensagem': 'Turno encerrado.'})
    except ValueError as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400


@auditorias_bp.route('/turno/cancelar/<int:turno_id>')
@perfil_required("admin")
def cancelar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    acao_id = turno.acao_id
    FotoAuditoria.query.filter_by(turno_id=turno_id).delete()
    db.session.delete(turno)
    db.session.commit()
    flash('Turno cancelado.', 'danger')
    return redirect(url_for('auditorias.turnos', acao_id=acao_id))


@auditorias_bp.route('/turno/editar/<int:turno_id>', methods=['POST'])
@perfil_required("admin")
def editar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    turno.equipe_id = request.form.get('equipe_id')
    turno.veiculo_id = request.form.get('veiculo_id')
    turno.observacoes = request.form.get('observacoes')
    db.session.commit()
    flash('Turno atualizado.', 'success')
    return redirect(url_for('auditorias.turnos', acao_id=turno.acao_id))


@auditorias_bp.route('/turno/excluir/<int:turno_id>')
@perfil_required("admin")
def excluir_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    try:
        FotoAuditoria.query.filter_by(turno_id=turno_id).delete()
        db.session.delete(turno)
        db.session.commit()
        return jsonify({'status': 'sucesso', 'mensagem': 'Turno excluído.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@auditorias_bp.route('/excluir/<int:foto_id>', methods=['POST'])
@perfil_required("admin")
def excluir_auditoria(foto_id):
    """
    Rota mantida por compatibilidade de URL.
    Opera sobre FotoAuditoria (fonte de verdade única após Passo 1).
    """
    foto = FotoAuditoria.query.get_or_404(foto_id)
    try:
        db.session.delete(foto)
        db.session.commit()
        flash('Registro excluído com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir registro.', 'danger')
    return redirect(url_for('auditorias.listar'))
