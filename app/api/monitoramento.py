from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.gps_log import GPSLog
from flask_login import current_user

bp = Blueprint("api_monitoramento", __name__, url_prefix="/api")


# RECEBER POSIÇÃO GPS
@bp.route("/gps", methods=["POST"])
def receber_gps():

    data = request.json

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")

    log = GPSLog(
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "ok"})


# 🔵 ROTA PARA PEGAR O RASTRO
@bp.route("/gps_rastro", methods=["GET"])
def gps_rastro():

    logs = (
        GPSLog.query
        .filter_by(user_id=current_user.id)
        .order_by(GPSLog.created_at.asc())
        .all()
    )

    pontos = []

    for log in logs:
        pontos.append({
            "lat": log.latitude,
            "lon": log.longitude,
            "accuracy": log.accuracy,
            "created_at": log.created_at.isoformat()
        })

    return jsonify({
        "user_id": current_user.id,
        "total_pontos": len(pontos),
        "pontos": pontos
    })