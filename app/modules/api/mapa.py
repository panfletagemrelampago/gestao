from flask import Blueprint, jsonify
from flask_login import login_required
from app.models.foto_auditoria import FotoAuditoria

bp = Blueprint('api_mapa', __name__)

@bp.route('/api/mapa/fotos')
@login_required
def fotos_mapa():
    fotos = FotoAuditoria.query.all()

    resultado = []

    for f in fotos:
        resultado.append({
            "lat": f.latitude,
            "lng": f.longitude,
            "img": f.url,
            "descricao": f.descricao,
            "data": f.data_hora.isoformat() if f.data_hora else None,
            "turno_id": f.turno_id
        })

    return jsonify(resultado)