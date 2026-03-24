from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.foto_auditoria import FotoAuditoria
from app.models.posicao_gps import PosicaoGps
from app.extensions import db
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_acoes_por_perfil, get_cliente_id_do_usuario
import math

mapa_bp = Blueprint('mapa', __name__)

# =============================
# Página do mapa
# =============================
@mapa_bp.route('/')
@perfil_required("admin", "funcionario", "cliente")
def index():
    """
    Exibe o mapa com ações filtradas por perfil:
    - admin: todas as ações
    - funcionario: ações em que é líder
    - cliente: ações vinculadas ao seu cliente_id
    """
    acoes = get_acoes_por_perfil()
    return render_template(
        "mapa/index.html",
        acoes=acoes
    )


# =============================
# 📸 LEGADO: FOTOS PARA O MAPA (ANTIGO)
# Atualizado com controlo de acesso por perfil e filtro de data
# =============================
@mapa_bp.route("/api/fotos")
@perfil_required("admin", "funcionario", "cliente")
def mapa_fotos():
    """
    Retorna fotos geolocalizadas para o mapa.
    Controlo de acesso por perfil:
    - admin: todas as fotos do dia (ou filtro de data)
    - funcionario: apenas as suas próprias fotos
    - cliente: apenas fotos vinculadas ao seu cliente_id
    """
    hoje = datetime.utcnow().date()
    data_inicio = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
    data_fim = datetime(hoje.year, hoje.month, hoje.day, 23, 59, 59)

    fotos_query = FotoAuditoria.query.filter(
        FotoAuditoria.data_hora >= data_inicio,
        FotoAuditoria.data_hora <= data_fim
    )

    if current_user.tipo_usuario == 'funcionario':
        fotos_query = fotos_query.filter(FotoAuditoria.usuario_id == current_user.id)
    elif current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id:
            return jsonify([])
        fotos_query = fotos_query.filter(FotoAuditoria.cliente_id == cliente_id)
    # admin: sem filtro adicional

    fotos = fotos_query.order_by(FotoAuditoria.data_hora.desc()).all()

    resultado = []
    for f in fotos:
        resultado.append({
            "id": f.id,
            "lat": f.latitude,
            "lng": f.longitude,
            "img": f.url,
            "descricao": f.descricao,
            "turno_id": f.turno_id,
            "data": f.data_hora.isoformat() if f.data_hora else None
        })

    return jsonify(resultado)


# =============================
# ⚠️ LEGADO: GPS ATUAL (DESATIVADO COMO PRINCIPAL)
# Atualizado: funcionário vê apenas o seu próprio rastro
# =============================
@mapa_bp.route("/api/gps/latest")
@perfil_required("admin", "funcionario")
def gps_latest():
    """
    Retorna as últimas posições GPS.
    - admin: todos os dispositivos
    - funcionario: apenas o seu próprio device_id
    """
    query = PosicaoGps.query.order_by(PosicaoGps.data_hora.desc()).limit(50)

    if current_user.tipo_usuario == 'funcionario':
        query = PosicaoGps.query.filter(
            PosicaoGps.device_id == str(current_user.id)
        ).order_by(PosicaoGps.data_hora.desc()).limit(50)

    logs = query.all()
    resultado = []

    for log in logs:
        if log.accuracy and log.accuracy > 50:
            continue
        resultado.append({
            "device_id": log.device_id,
            "latitude": log.latitude,
            "longitude": log.longitude,
            "accuracy": log.accuracy,
            "data_hora": log.data_hora.isoformat()
        })

    return jsonify(resultado)


# =============================
# ⚠️ LEGADO: HISTÓRICO GPS (RASTRO)
# Atualizado: funcionário só pode ver o seu próprio histórico
# =============================
@mapa_bp.route("/api/gps/historico/<string:device_id>")
@perfil_required("admin", "funcionario")
def gps_historico(device_id):
    """
    Retorna o histórico GPS de um dispositivo.
    - admin: pode ver qualquer device_id
    - funcionario: só pode ver o seu próprio device_id
    """
    # 🔐 Funcionário só pode consultar o seu próprio rastro
    if current_user.tipo_usuario == 'funcionario':
        if device_id != str(current_user.id):
            return jsonify({"erro": "Acesso negado"}), 403

    logs = (
        PosicaoGps.query
        .filter_by(device_id=device_id)
        .order_by(PosicaoGps.data_hora.asc())
        .limit(500)
        .all()
    )

    pontos = []
    ultimo = None

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(dlambda / 2) ** 2
        )

        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    for log in logs:

        if log.accuracy and log.accuracy > 50:
            continue

        atual = (log.latitude, log.longitude)

        if ultimo:
            dist = haversine(
                ultimo[0],
                ultimo[1],
                atual[0],
                atual[1]
            )
            if dist > 120:
                continue

        pontos.append({
            "lat": log.latitude,
            "lng": log.longitude,
            "accuracy": log.accuracy,
            "time": log.data_hora.timestamp()
        })

        ultimo = atual

    return jsonify(pontos)


# =============================
# 🆕 NOVO: FOTOS GEOLOCALIZADAS COM TO_DICT()
# Atualizado com controlo de acesso por perfil
# =============================
@mapa_bp.route('/api/mapa/fotos')
@perfil_required("admin", "funcionario", "cliente")
def get_fotos_mapa():
    """
    Retorna fotos geolocalizadas usando o método to_dict() do modelo.
    Controlo de acesso por perfil:
    - admin: todas as fotos
    - funcionario: apenas as suas próprias fotos
    - cliente: apenas fotos vinculadas ao seu cliente_id
    """
    fotos_query = FotoAuditoria.query

    if current_user.tipo_usuario == 'funcionario':
        fotos_query = fotos_query.filter(FotoAuditoria.usuario_id == current_user.id)
    elif current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id:
            return jsonify([])
        fotos_query = fotos_query.filter(FotoAuditoria.cliente_id == cliente_id)
    # admin: sem filtro adicional

    fotos = fotos_query.order_by(FotoAuditoria.data_hora.desc()).all()
    return jsonify([f.to_dict() for f in fotos])
