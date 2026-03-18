from flask import Blueprint, jsonify
from flask_login import login_required
from app.models.auditoria import Auditoria

bp = Blueprint('api_mapa', __name__)

@bp.route('/api/mapa/fotos')
@login_required
def fotos_mapa():
    auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).all()

    resultado = []

    for a in auditorias:
        if not a.latitude or not a.longitude:
            continue

        resultado.append({
            "lat": a.latitude,
            "lng": a.longitude,
            "img": a.foto_url,
            "descricao": a.descricao,
            "data": a.data_hora.isoformat() if a.data_hora else None,
            "id": a.id
        })

    return jsonify(resultado)