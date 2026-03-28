"""
Blueprint da API REST do sistema de gestão promocional.

REFATORAÇÃO (Passo 2):
- receber_gps() agora delega integralmente ao GpsService (filtro de ruído +
  validação de deslocamento improvável). Sem lógica de coordenadas na rota.
- Respostas de GPS, fotos e turnos usam Schemas Marshmallow (app/schemas.py)
  no lugar de dicionários montados manualmente.
- Removido import e uso do modelo legado Auditoria; mapa_dados() retorna
  apenas FotoAuditoria (campo 'auditorias_legadas' removido).
- Índices compostos gerados via migration (ver migrations/versions/).
"""
import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.posicao_gps import PosicaoGps
from app.models.veiculo import Veiculo
from app.models.acao_promocional import AcaoPromocional
from app.models.turno import Turno
from app.models.area_atuacao import AreaAtuacao
from app.models.foto_auditoria import FotoAuditoria
from app.models.equipe import Equipe
from app.services.gps_service import GpsService
from app.services.cloudinary_service import CloudinaryService
from app.extensions import db
from app.models.mapa_area import MapaArea
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_cliente_id_do_usuario
from app.schemas import (
    posicoes_gps_resumo_schema,
    fotos_auditoria_schema,
    fotos_mapa_schema,
    turnos_schema,
    turno_schema,
)

api_bp = Blueprint('api', __name__)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ─────────────────────────────────────────────────────────────────────────────
# GPS (Geolocation API)
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/gps', methods=['POST'])
@perfil_required("admin", "funcionario")
def receber_gps():
    """
    Endpoint para receber dados GPS do navegador via Geolocation API.
    Recebe JSON: { latitude, longitude, accuracy }

    Delega ao GpsService toda a lógica de filtragem (drift + impossible jump).
    """
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    lat = data.get('latitude')
    lon = data.get('longitude')
    acc = data.get('accuracy')

    if lat is None or lon is None:
        return jsonify({"erro": "Latitude e longitude são obrigatórios"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return jsonify({"erro": "Latitude e longitude devem ser números válidos"}), 400

    # Delegar ao GpsService (filtro de ruído + validação de deslocamento improvável)
    nova_posicao = GpsService.process_and_save_position(
        device_id=current_user.id,
        latitude=lat,
        longitude=lon,
        speed_knots=0.0,          # Browser Geolocation API não reporta velocidade
        battery=None,
        fix_time=_utcnow(),
    )

    if nova_posicao is None:
        # Ponto descartado por filtro (ruído ou salto impossível)
        return jsonify({"status": "descartado", "mensagem": "Ponto filtrado (ruído ou salto impossível)"}), 200

    return jsonify({"status": "sucesso", "id": nova_posicao.id}), 201


@api_bp.route('/gps/latest', methods=['GET'])
@perfil_required("admin", "funcionario")
def gps_latest():
    """
    Retorna as últimas posições de todos os dispositivos ativos nas últimas 24 horas.
    Resposta serializada via Marshmallow (PosicaoGpsResumoSchema).
    """
    tempo_limite = _utcnow() - timedelta(hours=24)

    subquery = db.session.query(
        PosicaoGps.device_id,
        db.func.max(PosicaoGps.data_hora).label('max_data_hora')
    ).filter(PosicaoGps.data_hora >= tempo_limite).group_by(PosicaoGps.device_id).subquery()

    ultimas_posicoes = db.session.query(PosicaoGps).join(
        subquery,
        db.and_(
            PosicaoGps.device_id == subquery.c.device_id,
            PosicaoGps.data_hora == subquery.c.max_data_hora
        )
    ).all()

    return jsonify(posicoes_gps_resumo_schema.dump(ultimas_posicoes))


@api_bp.route('/gps/historico/<string:device_id>', methods=['GET'])
@perfil_required("admin", "funcionario")
def historico_gps(device_id):
    """
    Retorna o histórico de posições GPS de um dispositivo.
    Parâmetros: horas (padrão 24).
    """
    horas = request.args.get('horas', 24, type=int)
    if horas <= 0 or horas > 168:
        return jsonify({"erro": "Parâmetro 'horas' deve estar entre 1 e 168"}), 400

    tempo_limite = _utcnow() - timedelta(hours=horas)

    posicoes = PosicaoGps.query.filter(
        PosicaoGps.device_id == device_id,
        PosicaoGps.data_hora >= tempo_limite
    ).order_by(PosicaoGps.data_hora.asc()).all()

    from app.schemas import posicoes_gps_schema
    return jsonify({
        "device_id": device_id,
        "total_pontos": len(posicoes),
        "pontos": posicoes_gps_schema.dump(posicoes)
    })


# ─────────────────────────────────────────────────────────────────────────────
# TURNOS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/turnos/iniciar', methods=['POST'])
@perfil_required("funcionario")
def iniciar_turno():
    data = request.get_json() or {}
    acao_id = data.get('acao_id')

    if not acao_id:
        return jsonify({"erro": "acao_id é obrigatório"}), 400

    try:
        from app.services.turno_service import TurnoService
        novo_turno = TurnoService.iniciar_turno(acao_id, current_user)
        return jsonify({
            "status": "sucesso",
            "turno_id": novo_turno.id,
            "inicio": novo_turno.inicio.isoformat(),
            "mensagem": "Turno iniciado com sucesso"
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro ao iniciar turno: {str(e)}"}), 500


@api_bp.route('/turnos/<int:turno_id>/pausar', methods=['POST'])
@perfil_required("funcionario")
def pausar_turno(turno_id):
    try:
        from app.services.turno_service import TurnoService
        TurnoService.pausar_turno(turno_id, current_user)
        return jsonify({"status": "sucesso", "mensagem": "Turno pausado com sucesso"})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route('/turnos/<int:turno_id>/retomar', methods=['POST'])
@perfil_required("funcionario")
def retomar_turno(turno_id):
    try:
        from app.services.turno_service import TurnoService
        TurnoService.retomar_turno(turno_id, current_user)
        return jsonify({"status": "sucesso", "mensagem": "Turno retomado com sucesso"})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route('/turnos/<int:turno_id>/encerrar', methods=['POST'])
@perfil_required("funcionario")
def encerrar_turno(turno_id):
    data = request.get_json() or {}
    obs = data.get('observacoes')
    try:
        from app.services.turno_service import TurnoService
        TurnoService.encerrar_turno(turno_id, current_user, obs)
        return jsonify({"status": "sucesso", "mensagem": "Turno encerrado com sucesso"})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@api_bp.route('/turnos/acao/<int:acao_id>', methods=['GET'])
@perfil_required("admin", "funcionario", "cliente")
def listar_turnos_acao(acao_id):
    """Lista todos os turnos de uma ação específica (Marshmallow)."""
    if current_user.tipo_usuario == 'cliente':
        acao = AcaoPromocional.query.get_or_404(acao_id)
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id or acao.cliente_id != cliente_id:
            return jsonify({"erro": "Acesso negado"}), 403

    turnos = Turno.query.filter_by(acao_id=acao_id).order_by(Turno.inicio.desc()).all()
    return jsonify({
        "acao_id": acao_id,
        "total": len(turnos),
        "turnos": turnos_schema.dump(turnos)
    })


# ─────────────────────────────────────────────────────────────────────────────
# ÁREAS DE ATUAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/areas/<int:acao_id>', methods=['GET'])
@perfil_required("admin", "funcionario", "cliente")
def listar_areas(acao_id):
    acao = AcaoPromocional.query.get_or_404(acao_id)

    if current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id or acao.cliente_id != cliente_id:
            return jsonify({"erro": "Acesso negado"}), 403

    areas = AreaAtuacao.query.filter_by(acao_id=acao_id).all()
    return jsonify({
        "acao_id": acao_id,
        "areas": [
            {
                "id": a.id,
                "nome": a.nome,
                "descricao": a.descricao,
                "geojson": a.get_geojson() if hasattr(a, 'get_geojson') else a.geojson,
                "cor": a.cor,
                "data_criacao": a.data_criacao.isoformat() if hasattr(a, 'data_criacao') and a.data_criacao else None
            }
            for a in areas
        ]
    })


@api_bp.route('/areas/<int:acao_id>', methods=['POST'])
@perfil_required("admin", "funcionario")
def salvar_area(acao_id):
    acao = AcaoPromocional.query.get_or_404(acao_id)
    data = request.get_json() or {}
    nome = data.get('nome', 'Área Principal')
    geojson = data.get('geojson')
    descricao = data.get('descricao')
    cor = data.get('cor', '#FF9E0C')

    if not geojson:
        return jsonify({"erro": "GeoJSON é obrigatório"}), 400

    if isinstance(geojson, dict):
        geojson_str = json.dumps(geojson)
    else:
        try:
            json.loads(geojson)
            geojson_str = geojson
        except (json.JSONDecodeError, TypeError):
            return jsonify({"erro": "GeoJSON inválido"}), 400

    try:
        nova_area = AreaAtuacao(
            acao_id=acao_id, nome=nome, descricao=descricao,
            geojson=geojson_str, cor=cor
        )
        db.session.add(nova_area)
        db.session.commit()
        return jsonify({"status": "sucesso", "area_id": nova_area.id,
                        "mensagem": f"Área '{nome}' salva com sucesso"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao salvar área: {str(e)}"}), 500


@api_bp.route('/areas/item/<int:area_id>', methods=['DELETE'])
@perfil_required("admin")
def deletar_area(area_id):
    area = AreaAtuacao.query.get_or_404(area_id)
    try:
        db.session.delete(area)
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Área removida"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao remover área: {str(e)}"}), 500


@api_bp.route("/areas/item/<int:area_id>", methods=["PUT"])
@perfil_required("admin", "funcionario")
def atualizar_area_atuacao(area_id):
    area = AreaAtuacao.query.get_or_404(area_id)
    data = request.get_json() or {}
    try:
        area.nome = data.get("nome", area.nome)
        area.descricao = data.get("descricao", area.descricao)
        area.cor = data.get("cor", area.cor)
        if "geojson" in data:
            new_geojson = data.get("geojson")
            if isinstance(new_geojson, dict):
                area.geojson = json.dumps(new_geojson)
            else:
                try:
                    json.loads(new_geojson)
                    area.geojson = new_geojson
                except (json.JSONDecodeError, TypeError):
                    return jsonify({"erro": "GeoJSON inválido"}), 400
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Área de atuação atualizada"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar área: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# ÁREAS DO MAPA (Desenhos Permanentes)
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route("/mapa/areas", methods=["GET"])
@perfil_required("admin", "funcionario", "cliente")
def get_mapa_areas():
    areas = MapaArea.query.all()
    return jsonify([
        {
            "id": area.id,
            "nome": area.nome,
            "descricao": area.descricao or '',
            "geojson": area.get_geojson() if hasattr(area, 'get_geojson') else area.geojson,
            "cor": area.cor or '#0d6efd',
            "criado_em": area.criado_em.isoformat() if hasattr(area, 'criado_em') and area.criado_em else None,
            "atualizado_em": area.atualizado_em.isoformat() if hasattr(area, 'atualizado_em') and area.atualizado_em else None
        }
        for area in areas
    ])


@api_bp.route("/mapa/areas", methods=["POST"])
@perfil_required("admin", "funcionario")
def post_mapa_area():
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    nome = data.get("nome", f"Área Desenhada {datetime.now().strftime('%Y%m%d%H%M%S')}")
    descricao = data.get("descricao", '')
    cor = data.get("cor", '#0d6efd')
    geojson_data = data.get("geojson")

    if not geojson_data:
        return jsonify({"erro": "GeoJSON é obrigatório"}), 400

    try:
        geojson_str = json.dumps(geojson_data) if isinstance(geojson_data, dict) else geojson_data
        json.loads(geojson_str)
    except (json.JSONDecodeError, TypeError):
        return jsonify({"erro": "GeoJSON inválido"}), 400

    try:
        nova_area = MapaArea(nome=nome, descricao=descricao, geojson=geojson_str, cor=cor)
        db.session.add(nova_area)
        db.session.commit()
        return jsonify({"status": "sucesso", "id": nova_area.id,
                        "mensagem": "Área salva com sucesso"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao salvar área: {str(e)}"}), 500


@api_bp.route("/mapa/areas/<int:area_id>", methods=["DELETE"])
@perfil_required("admin", "funcionario")
def delete_mapa_area(area_id):
    area = MapaArea.query.get_or_404(area_id)
    try:
        db.session.delete(area)
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Área removida com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao remover área: {str(e)}"}), 500


@api_bp.route("/mapa/areas/<int:area_id>", methods=["PUT"])
@perfil_required("admin", "funcionario")
def update_mapa_area(area_id):
    area = MapaArea.query.get_or_404(area_id)
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    try:
        if "nome" in data:
            area.nome = data["nome"]
        if "descricao" in data:
            area.descricao = data["descricao"]
        if "cor" in data:
            area.cor = data["cor"]
        if "geojson" in data:
            geojson_data = data["geojson"]
            try:
                area.geojson = json.dumps(geojson_data) if isinstance(geojson_data, dict) else geojson_data
                json.loads(area.geojson)
            except (json.JSONDecodeError, TypeError):
                return jsonify({"erro": "GeoJSON inválido"}), 400
        db.session.commit()
        return jsonify({"status": "sucesso", "id": area.id,
                        "mensagem": "Área atualizada com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar área: {str(e)}"}), 500


@api_bp.route('/areas/verificar', methods=['POST'])
@perfil_required("admin", "funcionario")
def verificar_ponto_na_area():
    data = request.get_json() or {}
    acao_id = data.get('acao_id')
    lat = data.get('latitude')
    lon = data.get('longitude')

    if not all([acao_id, lat, lon]):
        return jsonify({"erro": "acao_id, latitude e longitude são obrigatórios"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return jsonify({"erro": "Latitude e longitude devem ser números válidos"}), 400

    areas = AreaAtuacao.query.filter_by(acao_id=acao_id).all()
    if not areas:
        return jsonify({"dentro": None, "mensagem": "Nenhuma área definida para esta ação"})

    for area in areas:
        if hasattr(area, 'ponto_dentro_da_area') and area.ponto_dentro_da_area(lat, lon):
            return jsonify({"dentro": True, "area_id": area.id, "area_nome": area.nome})

    return jsonify({"dentro": False, "mensagem": "Ponto fora de todas as áreas definidas"})


# ─────────────────────────────────────────────────────────────────────────────
# FOTOS DE AUDITORIA
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/fotos/enviar', methods=['POST'])
@perfil_required("admin", "funcionario")
def enviar_foto():
    """
    Recebe uma foto com geolocalização e a associa a um turno.
    Campos do formulário: turno_id, latitude, longitude, descricao (opcional), foto (arquivo).
    """
    turno_id = request.form.get('turno_id', type=int)
    lat = request.form.get('latitude', type=float)
    lon = request.form.get('longitude', type=float)
    descricao = request.form.get('descricao')
    foto = request.files.get('foto')

    if not turno_id:
        return jsonify({"erro": "turno_id é obrigatório"}), 400
    if lat is None or lon is None:
        return jsonify({"erro": "Localização GPS obrigatória para envio de fotos"}), 400
    if not foto:
        return jsonify({"erro": "Arquivo de foto é obrigatório"}), 400

    turno = Turno.query.get(turno_id)
    if not turno:
        return jsonify({"erro": "Turno não encontrado"}), 404
    if turno.status == 'encerrado':
        return jsonify({"erro": "Não é possível enviar fotos para um turno encerrado"}), 400

    foto_url = CloudinaryService.upload_image(foto, folder="auditorias_campo")
    if not foto_url:
        return jsonify({"erro": "Falha no upload da foto"}), 500

    dentro_da_area = None
    try:
        areas = AreaAtuacao.query.filter_by(acao_id=turno.acao_id).all()
        if areas:
            dentro_da_area = any(
                hasattr(a, 'ponto_dentro_da_area') and a.ponto_dentro_da_area(lat, lon)
                for a in areas
            )

        nova_foto = FotoAuditoria(
            turno_id=turno_id,
            acao_id=turno.acao_id,
            url=foto_url,
            latitude=lat,
            longitude=lon,
            descricao=descricao,
            dentro_da_area=dentro_da_area,
            data_hora=_utcnow(),
            usuario_id=current_user.id,
            cliente_id=turno.acao.cliente_id if turno.acao else None
        )
        db.session.add(nova_foto)
        db.session.commit()

        return jsonify({
            "status": "sucesso",
            "foto_id": nova_foto.id,
            "url": foto_url,
            "dentro_da_area": dentro_da_area,
            "mensagem": "Foto enviada com sucesso"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao salvar foto: {str(e)}"}), 500


@api_bp.route('/fotos/turno/<int:turno_id>', methods=['GET'])
@perfil_required("admin", "funcionario", "cliente")
def fotos_do_turno(turno_id):
    """Retorna todas as fotos de um turno específico (Marshmallow)."""
    turno = Turno.query.get_or_404(turno_id)

    if current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id or turno.acao.cliente_id != cliente_id:
            return jsonify({"erro": "Acesso negado"}), 403

    fotos = FotoAuditoria.query.filter_by(turno_id=turno_id).order_by(
        FotoAuditoria.data_hora.asc()
    ).all()

    return jsonify({
        "turno_id": turno_id,
        "total_fotos": len(fotos),
        "fotos": fotos_auditoria_schema.dump(fotos)
    })


# ─────────────────────────────────────────────────────────────────────────────
# MAPA (dados consolidados para o Leaflet)
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/mapa/dados')
@perfil_required("admin", "funcionario", "cliente")
def mapa_dados():
    """
    Retorna dados JSON consolidados para o mapa Leaflet.
    Inclui rastros GPS, fotos geolocalizadas, áreas de atuação e veículos.
    Respostas de fotos e GPS usam Marshmallow.
    """
    acao_id = request.args.get('acao_id', type=int)
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')

    hoje = _utcnow().date()
    try:
        if data_inicio_str:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        else:
            data_inicio = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)

        if data_fim_str:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d') + timedelta(hours=23, minutes=59, seconds=59)
        else:
            data_fim = datetime(hoje.year, hoje.month, hoje.day, 23, 59, 59)
    except ValueError:
        return jsonify({"erro": "Formato de data inválido. Use YYYY-MM-DD."}), 400

    # Controle de acesso por perfil
    if current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id:
            return jsonify({"veiculos": [], "fotos": [], "rastros_gps": {}, "areas": []})
        filtro_acoes = [a.id for a in AcaoPromocional.query.filter_by(cliente_id=cliente_id).all()]
        filtro_usuario_id = None
        filtro_cliente_id = cliente_id
    elif current_user.tipo_usuario == 'funcionario':
        filtro_acoes = None
        filtro_usuario_id = current_user.id
        filtro_cliente_id = None
    else:
        filtro_acoes = None
        filtro_usuario_id = None
        filtro_cliente_id = None

    # Fotos (FotoAuditoria — fonte única)
    fotos_query = FotoAuditoria.query.filter(
        FotoAuditoria.data_hora >= data_inicio,
        FotoAuditoria.data_hora <= data_fim
    )
    if acao_id:
        fotos_query = fotos_query.join(Turno, FotoAuditoria.turno_id == Turno.id, isouter=True).filter(
            Turno.acao_id == acao_id
        )
    elif filtro_usuario_id is not None:
        fotos_query = fotos_query.filter(FotoAuditoria.usuario_id == filtro_usuario_id)
    elif filtro_cliente_id is not None:
        fotos_query = fotos_query.filter(FotoAuditoria.cliente_id == filtro_cliente_id)
    fotos = fotos_query.all()

    # Rastros GPS
    rastros_gps = {}
    if current_user.tipo_usuario != 'cliente':
        posicoes_query = PosicaoGps.query.filter(
            PosicaoGps.data_hora >= data_inicio,
            PosicaoGps.data_hora <= data_fim
        )
        if filtro_usuario_id is not None:
            posicoes_query = posicoes_query.filter(
                PosicaoGps.device_id == str(filtro_usuario_id)
            )
        posicoes = posicoes_query.order_by(PosicaoGps.data_hora.asc()).all()
        for p in posicoes:
            key = str(p.device_id)
            if key not in rastros_gps:
                rastros_gps[key] = []
            rastros_gps[key].append([p.latitude, p.longitude])

    # Veículos
    veiculos = []
    if current_user.tipo_usuario != 'cliente':
        veiculos = Veiculo.query.all()

    # Áreas de Atuação
    areas_query = AreaAtuacao.query
    if acao_id:
        areas_query = areas_query.filter_by(acao_id=acao_id)
    elif filtro_acoes is not None:
        areas_query = areas_query.filter(AreaAtuacao.acao_id.in_(filtro_acoes))
    areas = areas_query.all()

    # Overlays persistentes do mapa
    overlays = []
    if current_user.tipo_usuario in ('admin', 'funcionario'):
        overlays = [
            {
                "id": o.id,
                "nome": o.nome,
                "geojson": o.get_geojson() if hasattr(o, 'get_geojson') else o.geojson
            }
            for o in MapaArea.query.all()
        ]

    return jsonify({
        "filtro": {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "acao_id": acao_id
        },
        "veiculos": [
            {"id": v.id, "placa": v.placa, "modelo": v.modelo, "status": v.status}
            for v in veiculos
        ],
        "fotos": fotos_mapa_schema.dump(fotos),
        "rastros_gps": rastros_gps,
        "areas": [
            {
                "id": a.id,
                "nome": a.nome,
                "geojson": a.get_geojson() if hasattr(a, 'get_geojson') else a.geojson,
                "cor": a.cor,
                "acao_id": a.acao_id
            }
            for a in areas
        ],
        "overlays": overlays
    })


@api_bp.route('/mapa/dados/acao/<int:acao_id>')
@perfil_required("admin", "funcionario", "cliente")
def mapa_dados_acao(acao_id):
    """
    Retorna dados completos do mapa para uma ação específica.
    """
    acao = AcaoPromocional.query.get_or_404(acao_id)

    if current_user.tipo_usuario == 'cliente':
        cliente_id = get_cliente_id_do_usuario(current_user)
        if not cliente_id or acao.cliente_id != cliente_id:
            return jsonify({"erro": "Acesso negado"}), 403

    turnos = Turno.query.filter_by(acao_id=acao_id).all()
    areas = AreaAtuacao.query.filter_by(acao_id=acao_id).all()
    fotos = FotoAuditoria.query.join(Turno).filter(Turno.acao_id == acao_id).all()

    rastros_por_turno = {}
    from app.models.user import User

    for turno in turnos:
        if not turno.inicio:
            continue
        equipe = turno.equipe
        if not equipe:
            continue

        membros_com_device = User.query.filter(
            User.equipe_id == equipe.id,
            User.device_id.isnot(None)
        ).all()

        pontos_turno = []
        for usuario in membros_com_device:
            fim = turno.fim or _utcnow()
            posicoes = PosicaoGps.query.filter(
                PosicaoGps.device_id == usuario.device_id,
                PosicaoGps.data_hora >= turno.inicio,
                PosicaoGps.data_hora <= fim
            ).order_by(PosicaoGps.data_hora.asc()).all()
            pontos_turno.extend([[p.latitude, p.longitude] for p in posicoes])

        if pontos_turno:
            rastros_por_turno[str(turno.id)] = {
                "equipe": equipe.nome,
                "veiculo": turno.veiculo.placa if turno.veiculo else None,
                "status": turno.status,
                "pontos": pontos_turno
            }

    return jsonify({
        "acao": {
            "id": acao.id,
            "local_alvo": acao.nome_exibicao,
            "bairro": acao.bairro,
            "cidade": acao.cidade,
            "data": acao.data.isoformat() if acao.data else None,
            "status": acao.status,
            "cliente": acao.cliente.nome_empresa if acao.cliente else None
        },
        "turnos": turnos_schema.dump(turnos),
        "rastros_por_turno": rastros_por_turno,
        "fotos": fotos_mapa_schema.dump(fotos),
        "areas": [
            {
                "id": a.id,
                "nome": a.nome,
                "geojson": a.get_geojson() if hasattr(a, 'get_geojson') else a.geojson,
                "cor": a.cor
            }
            for a in areas
        ]
    })
