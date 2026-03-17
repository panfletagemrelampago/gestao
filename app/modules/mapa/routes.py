from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
from app.models.gps_position import GpsPosition
from app.extensions import db
import requests
import os

mapa_bp = Blueprint('mapa', __name__)

# =============================
# Página do mapa
# =============================
@mapa_bp.route('/')
@login_required
def index():

    # FILTRO DE AÇÕES
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
        GpsPosition.query
        .order_by(GPSLog.created_at.desc())
        .limit(50)
        .all()
    )

    resultado = []

    for log in logs:
        resultado.append({
            "user_id": log.user_id,
            "latitude": log.latitude,
            "longitude": log.longitude,
            "data": log.created_at
        })

    return jsonify(resultado)


# =============================
# HISTÓRICO (RASTRO)
# =============================
@mapa_bp.route("/api/gps/historico")
@login_required
def gps_historico():

    logs = (
        GpsPosition.query
        .filter_by(user_id=current_user.id)
        .order_by(GPSLog.created_at.asc())
        .limit(300)
        .all()
    )

    resultado = []

    for log in logs:
        resultado.append({
            "lat": log.latitude,
            "lng": log.longitude
        })

    return jsonify(resultado)