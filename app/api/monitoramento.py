from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.gps_log import GPSLog
from flask_login import current_user
from datetime import datetime
import math

bp = Blueprint("api_monitoramento", __name__, url_prefix="/api")


# =============================
# FUNÇÃO DISTÂNCIA (Haversine)
# =============================
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


# =============================
# RECEBER POSIÇÃO GPS
# =============================
@bp.route("/gps", methods=["POST"])
def receber_gps():

    if not current_user.is_authenticated:
        return jsonify({"erro": "não autenticado"}), 401

    data = request.json

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")

    # 🚫 validar dados básicos
    if latitude is None or longitude is None:
        return jsonify({"erro": "dados inválidos"}), 400

    # 🚫 ignorar gps ruim
    if accuracy and accuracy > 40:
        return jsonify({"status": "ignorado_precisao_ruim"})

    # 🔍 pegar último ponto do usuário
    ultimo = (
        GPSLog.query
        .filter_by(user_id=current_user.id)
        .order_by(GPSLog.created_at.desc())
        .first()
    )

    if ultimo:

        dist = haversine(
            ultimo.latitude,
            ultimo.longitude,
            latitude,
            longitude
        )

        # 🚫 ignorar salto absurdo
        if dist > 150:
            return jsonify({"status": "ignorado_salto"})

    # ✅ salvar posição válida
    log = GPSLog(
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        created_at=datetime.utcnow()
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "ok"})


# =============================
# RASTRO GPS
# =============================
@bp.route("/gps_rastro", methods=["GET"])
def gps_rastro():

    if not current_user.is_authenticated:
        return jsonify({"erro": "não autenticado"}), 401

    logs = (
        GPSLog.query
        .filter_by(user_id=current_user.id)
        .order_by(GPSLog.created_at.asc())
        .limit(500)
        .all()
    )

    pontos = []
    ultimo = None

    for log in logs:

        # ignorar precisão ruim
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
            "time": log.created_at.timestamp()
        })

        ultimo = atual

    return jsonify({
        "user_id": current_user.id,
        "total_pontos": len(pontos),
        "pontos": pontos
    })