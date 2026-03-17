from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.posicao_gps import PosicaoGps
from app.extensions import db
import math

mapa_bp = Blueprint('mapa', __name__)

# =============================
# Página do mapa
# =============================
@mapa_bp.route('/')
@login_required
def index():

    if current_user.tipo_usuario == 'cliente':
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        acoes = AcaoPromocional.query.filter_by(cliente_id=cliente.id).all() if cliente else []

    elif current_user.tipo_usuario == 'equipe':
        acoes = AcaoPromocional.query.filter_by(lider_equipe_id=current_user.id).all()

    else:
        acoes = AcaoPromocional.query.order_by(AcaoPromocional.data.desc()).all()

    return render_template(
        "mapa/index.html",
        acoes=acoes
    )


# =============================
# GPS ATUAL
# =============================
@mapa_bp.route("/api/gps/latest")
@login_required
def gps_latest():

    logs = (
        PosicaoGps.query
        .order_by(PosicaoGps.data_hora.desc())
        .limit(50)
        .all()
    )

    resultado = []

    for log in logs:

        # ignorar gps muito impreciso
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
# HISTÓRICO GPS (RASTRO)
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

        # filtro de precisão
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

            # filtrar salto absurdo
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