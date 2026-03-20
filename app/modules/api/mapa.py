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
        if not a.latitude or not a.longitude: continue
        periodo_turno = a.acao.turno if a.acao else "N/A"
        resultado.append({
            "lat": a.latitude, "lng": a.longitude, "img": a.foto_url,
            "descricao": a.descricao, "data": a.data_hora.isoformat(),
            "id": a.id, "turno_id": periodo_turno
        })
    return jsonify(resultado)

@bp.route('/api/mapa/areas')
@login_required
def areas_mapa():
    from app.models.area_atuacao import AreaAtuacao
    areas = AreaAtuacao.query.all()
    resultado = []
    for area in areas:
        geojson = area.get_geojson()
        if geojson:
            resultado.append({
                "id": area.id, "nome": area.nome, "descricao": area.descricao,
                "geojson": geojson, "cor": area.cor or "#0d6efd"
            })
    return jsonify(resultado)
