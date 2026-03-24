from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import current_user
from app.models.auditoria import Auditoria
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_cliente_id_do_usuario

bp = Blueprint('api_mapa', __name__)


@bp.route('/api/mapa/fotos')
@perfil_required("admin", "funcionario", "cliente")
def fotos_mapa():
    """
    Retorna fotos (Auditoria legada) para o mapa.
    Controlo de acesso por perfil:
    - admin: todas as fotos
    - funcionario: apenas as suas próprias (user_id == current_user.id)
    - cliente: apenas fotos das ações vinculadas ao seu cliente_id
    """
    from app.models.acao_promocional import AcaoPromocional

    query = Auditoria.query.order_by(Auditoria.data_hora.desc())

    if current_user.tipo_usuario == 'funcionario':
        query = query.filter(Auditoria.user_id == current_user.id)
    elif current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id:
            return jsonify([])
        acoes_ids = [a.id for a in AcaoPromocional.query.filter_by(cliente_id=cliente_id).all()]
        query = query.filter(Auditoria.acao_id.in_(acoes_ids))
    # admin: sem filtro adicional

    auditorias = query.all()
    resultado = []
    for a in auditorias:
        if not a.latitude or not a.longitude:
            continue
        periodo_turno = a.acao.turno if a.acao else "N/A"
        resultado.append({
            "lat": a.latitude, "lng": a.longitude, "img": a.foto_url,
            "descricao": a.descricao, "data": a.data_hora.isoformat(),
            "id": a.id, "turno_id": periodo_turno
        })
    return jsonify(resultado)


@bp.route('/api/mapa/areas')
@perfil_required("admin", "funcionario", "cliente")
def areas_mapa():
    """
    Retorna áreas de atuação para o mapa.
    - cliente: apenas áreas das suas próprias ações
    - funcionario/admin: todas as áreas
    """
    from app.models.area_atuacao import AreaAtuacao
    from app.models.acao_promocional import AcaoPromocional

    query = AreaAtuacao.query

    if current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id:
            return jsonify([])
        acoes_ids = [a.id for a in AcaoPromocional.query.filter_by(cliente_id=cliente_id).all()]
        query = query.filter(AreaAtuacao.acao_id.in_(acoes_ids))

    areas = query.all()
    resultado = []
    for area in areas:
        geojson = area.get_geojson()
        if geojson:
            resultado.append({
                "id": area.id, "nome": area.nome, "descricao": area.descricao,
                "geojson": geojson, "cor": area.cor or "#0d6efd"
            })
    return jsonify(resultado)
