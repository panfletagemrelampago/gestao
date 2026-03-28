"""
Blueprint api_mapa: endpoints de mapa para fotos e áreas.

REFATORAÇÃO (Passo 1 + Passo 2):
- fotos_mapa() migrado de Auditoria (legado) para FotoAuditoria (fonte única).
- Resposta serializada via FotoAuditoriaMapaSchema (Marshmallow).
- Removido import de Auditoria.
"""
import json
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_login import current_user
from app.models.foto_auditoria import FotoAuditoria
from app.models.mapa_area import MapaArea
from app.extensions import db
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_cliente_id_do_usuario
from app.schemas import fotos_mapa_schema

bp = Blueprint('api_mapa', __name__)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@bp.route('/api/mapa/fotos')
@perfil_required("admin", "funcionario", "cliente")
def fotos_mapa():
    """
    Retorna fotos de campo (FotoAuditoria) para o mapa Leaflet.
    Controle de acesso por perfil:
    - admin: todas as fotos
    - funcionario: apenas as suas próprias (usuario_id == current_user.id)
    - cliente: apenas fotos das ações vinculadas ao seu cliente_id
    Resposta serializada via Marshmallow (FotoAuditoriaMapaSchema).
    """
    from app.models.acao_promocional import AcaoPromocional

    query = FotoAuditoria.query.order_by(FotoAuditoria.data_hora.desc())

    if current_user.tipo_usuario == 'funcionario':
        query = query.filter(FotoAuditoria.usuario_id == current_user.id)
    elif current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id:
            return jsonify([])
        query = query.filter(FotoAuditoria.cliente_id == cliente_id)
    # admin: sem filtro adicional

    fotos = query.filter(
        FotoAuditoria.latitude.isnot(None),
        FotoAuditoria.longitude.isnot(None)
    ).all()

    return jsonify(fotos_mapa_schema.dump(fotos))


@bp.route('/api/mapa/areas', methods=['GET'])
@perfil_required("admin", "funcionario", "cliente")
def areas_mapa():
    """
    Retorna áreas de atuação (MapaArea) para o mapa.
    - cliente: não vê overlays de desenho livre (MapaArea)
    - funcionario/admin: todas as áreas
    """
    if current_user.tipo_usuario == 'cliente':
        return jsonify([])

    areas = MapaArea.query.all()
    resultado = []
    for area in areas:
        geojson = area.get_geojson()
        if geojson:
            resultado.append({
                "id": area.id,
                "nome": area.nome,
                "descricao": area.descricao,
                "geojson": geojson,
                "cor": area.cor or "#0d6efd"
            })
    return jsonify(resultado)


@bp.route('/api/mapa/areas', methods=['POST'])
@perfil_required("admin", "funcionario")
def criar_area_mapa():
    """Cria uma nova área no mapa."""
    data = request.get_json()
    if not data or 'geojson' not in data:
        return jsonify({"status": "erro", "erro": "Dados GeoJSON obrigatórios"}), 400

    try:
        nova_area = MapaArea(
            nome=data.get('nome', f"Área de {_utcnow().strftime('%Y-%m-%d %H:%M')}"),
            descricao=data.get('descricao', ''),
            geojson=json.dumps(data['geojson']),
            cor=data.get('cor', '#0d6efd')
        )
        db.session.add(nova_area)
        db.session.commit()
        return jsonify({"status": "sucesso", "id": nova_area.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "erro", "erro": str(e)}), 500


@bp.route('/api/mapa/areas/<int:area_id>', methods=['PUT'])
@perfil_required("admin", "funcionario")
def atualizar_area_mapa(area_id):
    """Atualiza uma área existente no mapa."""
    area = MapaArea.query.get_or_404(area_id)
    data = request.get_json()

    if not data:
        return jsonify({"status": "erro", "erro": "Nenhum dado fornecido"}), 400

    try:
        if 'nome' in data:
            area.nome = data['nome']
        if 'descricao' in data:
            area.descricao = data['descricao']
        if 'geojson' in data:
            area.geojson = json.dumps(data['geojson'])
        if 'cor' in data:
            area.cor = data['cor']

        db.session.commit()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "erro", "erro": str(e)}), 500


@bp.route('/api/mapa/areas/<int:area_id>', methods=['DELETE'])
@perfil_required("admin", "funcionario")
def excluir_area_mapa(area_id):
    """Exclui uma área do mapa."""
    area = MapaArea.query.get_or_404(area_id)
    try:
        db.session.delete(area)
        db.session.commit()
        return jsonify({"status": "sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "erro", "erro": str(e)}), 500
