"""
Blueprint do módulo de auditorias de campo.
Gerencia o registro de auditorias, turnos de campo e geração de relatórios.
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
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
from app.decorators.auth_decorators import perfil_required

auditorias_bp = Blueprint('auditorias', __name__)

# =============================
# HELPER: CONVERTER PARA TIMEZONE LOCAL (GMT-3)
# =============================
def get_local_now():
    """Retorna datetime atual no fuso de Cuiabá (GMT-4) sem usar pytz"""
    # UTC -> Cuiabá (GMT-4)
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-4))).replace(tzinfo=None)

def to_local_tz(dt):
    """Converte um datetime UTC para local (GMT-4)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=-4))).replace(tzinfo=None)


# =============================
# LISTAR AUDITORIAS
# =============================
@auditorias_bp.route('/')
@perfil_required("admin", "funcionario")
def listar():
    """
    Lista auditorias conforme o perfil:
    - admin: todas as auditorias
    - funcionario: apenas as que ele registrou
    Clientes não têm acesso direto a esta rota (acessam via /cliente/acao/<id>).
    """
    if current_user.tipo_usuario == 'admin':
        auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).all()
    else:  # funcionario
        auditorias = Auditoria.query.filter_by(user_id=current_user.id).order_by(
            Auditoria.data_hora.desc()
        ).all()

    return render_template('auditorias/listar.html', auditorias=auditorias)


# =============================
# REGISTRAR FOTO (COM TURNO)
# =============================
@auditorias_bp.route('/registrar', methods=['GET', 'POST'])
@perfil_required("admin", "funcionario")
def registrar():
    # Buscar ações agrupadas por cliente para o seletor melhorado
    acoes_ativas = AcaoPromocional.query.filter(
        AcaoPromocional.status.in_(['Planejada', 'Em Andamento'])
    ).order_by(AcaoPromocional.cliente_id, AcaoPromocional.data.desc()).all()

    # Agrupar por cliente
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

        # 🔥 TURNO ATIVO (GARANTIR EXISTÊNCIA)
        turno_ativo = Turno.query.filter_by(
            acao_id=acao_id,
            status='ativo'
        ).first()

        if not turno_ativo:
            # Lógica de busca de veículo robusta para criação automática
            veiculo_vinculado = Veiculo.query.filter_by(motorista_id=acao.lider_equipe_id).first()
            if not veiculo_vinculado and acao.lider:
                nome_lider = acao.lider.nome.split()[0]
                veiculo_vinculado = Veiculo.query.filter(Veiculo.modelo.ilike(f"%{nome_lider}%")).first()
            
            if not veiculo_vinculado:
                veiculo_vinculado = Veiculo.query.filter_by(status=True).first()
                
            veiculo_id = veiculo_vinculado.id if veiculo_vinculado else None
            
            turno_ativo = Turno(
                acao_id=acao_id,
                equipe_id=acao.lider_equipe_id,
                veiculo_id=veiculo_id,
                status='ativo'
            )
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
                data_hora=get_local_now()
            )
            db.session.add(nova_auditoria)

            nova_foto = FotoAuditoria(
                url=foto_url,
                latitude=lat,
                longitude=lon,
                descricao=descricao,
                data_hora=get_local_now(),
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

    return render_template('auditorias/registrar.html', acoes=acoes_ativas, clientes_acoes=clientes_acoes)


# =============================
# TELA DE TURNOS
# =============================
@auditorias_bp.route('/turnos/<int:acao_id>')
@perfil_required("admin", "funcionario")
def turnos(acao_id):
    acao = AcaoPromocional.query.get_or_404(acao_id)

    # Forçar carregamento do líder para garantir vínculo do veículo
    if acao.lider_equipe_id and not acao.lider:
        acao.lider = Equipe.query.get(acao.lider_equipe_id)

    # Funcionário só pode ver turnos de ações em que é líder
    if current_user.tipo_usuario == 'funcionario':
        if acao.lider_equipe_id != current_user.id:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('auditorias.listar'))

    equipes = Equipe.query.filter_by(status=True).all()
    veiculos = Veiculo.query.filter_by(status=True).all()
    turnos_lista = Turno.query.filter_by(acao_id=acao_id).order_by(Turno.inicio.desc()).all()

    # LÓGICA DE VÍNCULO DE VEÍCULO INFALÍVEL
    veiculo_lider = None
    if acao.lider_equipe_id:
        veiculo_lider = Veiculo.query.filter_by(motorista_id=acao.lider_equipe_id).first()
        if not veiculo_lider and acao.lider:
            nome_lider = acao.lider.nome.split()[0]
            veiculo_lider = Veiculo.query.filter(Veiculo.modelo.ilike(f"%{nome_lider}%")).first()
        if not veiculo_lider:
            veiculo_lider = Veiculo.query.filter_by(status=True).first()

    return render_template(
        'auditorias/turnos.html',
        acao=acao,
        equipes=equipes,
        veiculos=veiculos,
        turnos=turnos_lista,
        veiculo_lider=veiculo_lider
    )


# =============================
# RELATÓRIO
# =============================
@auditorias_bp.route('/relatorio/<int:acao_id>')
@perfil_required("admin", "funcionario", "cliente")
def relatorio(acao_id):
    """
    Relatório de auditoria de uma ação.
    Clientes só podem ver relatórios das suas próprias ações (verificado por cliente_id).
    """
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
        agora=get_local_now()
    )


# =============================
# TURNOS (CRUD)
# =============================
@auditorias_bp.route('/turno/iniciar/<int:acao_id>', methods=['POST'])
@perfil_required("admin", "funcionario")
def iniciar_turno(acao_id):
    acao = AcaoPromocional.query.get_or_404(acao_id)
    Turno.query.filter_by(acao_id=acao_id, status='ativo').update({
        'status': 'encerrado', 
        'fim': get_local_now()
    })

    # Busca robusta de veículo
    veiculo_vinculado = Veiculo.query.filter_by(motorista_id=acao.lider_equipe_id).first()
    if not veiculo_vinculado and acao.lider:
        nome_lider = acao.lider.nome.split()[0]
        veiculo_vinculado = Veiculo.query.filter(Veiculo.modelo.ilike(f"%{nome_lider}%")).first()
    if not veiculo_vinculado:
        veiculo_vinculado = Veiculo.query.filter_by(status=True).first()
        
    veiculo_id = veiculo_vinculado.id if veiculo_vinculado else None

    turno = Turno(
        acao_id=acao_id,
        equipe_id=acao.lider_equipe_id,
        veiculo_id=veiculo_id,
        status='ativo'
    )
    db.session.add(turno)
    db.session.commit()
    flash('Turno iniciado!', 'success')
    return redirect(url_for('auditorias.turnos', acao_id=acao_id))


@auditorias_bp.route('/turno/encerrar/<int:turno_id>')
@perfil_required("admin", "funcionario")
def encerrar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    turno.status = 'encerrado'
    turno.fim = get_local_now()
    db.session.commit()
    # Retornar JSON para compatibilidade com fetch() do frontend
    return jsonify({'status': 'sucesso', 'mensagem': 'Turno encerrado.'})


@auditorias_bp.route('/turno/retomar/<int:turno_id>')
@perfil_required("admin", "funcionario")
def retomar_turno(turno_id):
    """Retoma um turno que estava pausado/encerrado, reativando-o."""
    turno = Turno.query.get_or_404(turno_id)
    acao_id = turno.acao_id

    # Encerrar qualquer turno ativo antes de retomar este
    Turno.query.filter_by(acao_id=acao_id, status='ativo').update({
        'status': 'encerrado',
        'fim': get_local_now()
    })

    # Retomar the turno selecionado
    turno.status = 'ativo'
    turno.fim = None  # Limpa o horário de fim ao retomar
    db.session.commit()

    return jsonify({'status': 'sucesso', 'mensagem': 'Turno retomado com sucesso.'})


@auditorias_bp.route('/turno/cancelar/<int:turno_id>')
@perfil_required("admin")
def cancelar_turno(turno_id):
    turno = Turno.query.get_or_404(turno_id)
    acao_id = turno.acao_id
    # Excluir fotos vinculadas ao turno antes de excluir o turno
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
    acao_id = turno.acao_id
    try:
        # Excluir fotos vinculadas ao turno antes de excluir o turno
        FotoAuditoria.query.filter_by(turno_id=turno_id).delete()
        db.session.delete(turno)
        db.session.commit()
        return jsonify({'status': 'sucesso', 'mensagem': 'Turno excluído.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@auditorias_bp.route('/excluir/<int:auditoria_id>', methods=['POST'])
@perfil_required("admin")
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
