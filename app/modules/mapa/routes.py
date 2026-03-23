from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.foto_auditoria import FotoAuditoria
from app.models.posicao_gps import PosicaoGps
from app.extensions import db
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_acoes_por_perfil
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
# =============================
@mapa_bp.route("/api/fotos")
@login_required
def mapa_fotos():

    fotos = FotoAuditoria.query.order_by(FotoAuditoria.data_hora.desc()).all()

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
# =============================
@mapa_bp.route("/api/gps/latest")
@login_required
def gps_latest():

    # ⚠️ Mantido apenas por compatibilidade
    logs = (
        PosicaoGps.query
        .order_by(PosicaoGps.data_hora.desc())
        .limit(50)
        .all()
    )

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
# =============================
@mapa_bp.route("/api/gps/historico/<string:device_id>")
@login_required
def gps_historico(device_id):

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
# =============================
@mapa_bp.route('/api/mapa/fotos')
@login_required
def get_fotos_mapa():
    """
    Retorna fotos geolocalizadas usando o método to_dict() do modelo.
    Certifique-se de que o modelo FotoAuditoria tem o método to_dict() implementado.
    """
    fotos = FotoAuditoria.query.order_by(FotoAuditoria.data_hora.desc()).all()
    return jsonify([f.to_dict() for f in fotos])