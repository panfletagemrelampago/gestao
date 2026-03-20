from flask import Blueprint, jsonify
from flask_login import login_required
from app.models.auditoria import Auditoria

bp = Blueprint('api_mapa', __name__)

@bp.route('/api/mapa/fotos')
@login_required
def fotos_mapa():
    # Buscar todas as auditorias
    auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).all()

    resultado = []

    # Importar FotoAuditoria para buscar o vínculo com o turno
    from app.models.foto_auditoria import FotoAuditoria
    
    for a in auditorias:
        if not a.latitude or not a.longitude:
            continue

        # Buscar o ID do turno vinculado a esta auditoria na tabela fotos_auditoria
        # (onde o vínculo com o turno realmente existe no seu banco)
        foto_registro = FotoAuditoria.query.filter_by(url=a.foto_url).first()
        turno_id = foto_registro.turno_id if foto_registro else "N/A"

        resultado.append({
            "lat": a.latitude,
            "lng": a.longitude,
            "img": a.foto_url,
            "descricao": a.descricao,
            "data": a.data_hora.isoformat() if a.data_hora else None,
            "id": a.id,
            "turno_id": turno_id
        })

    return jsonify(resultado)
