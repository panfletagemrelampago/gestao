"""
Blueprint da API REST do sistema de gestão promocional.
Fornece endpoints para receber dados do GPS (Browser Geolocation), gerenciar turnos,
áreas de atuação, fotos geolocalizadas e dados do mapa Leaflet.
"""
import json
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.posicao_gps import PosicaoGps
from app.models.auditoria import Auditoria
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
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GPS (Geolocation API)
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/gps', methods=['POST'])
@login_required
def receber_gps():
    """
    Endpoint para receber dados GPS do navegador via Geolocation API.
    Recebe JSON: { latitude, longitude, accuracy }
    """
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    lat = data.get('latitude')
    lon = data.get('longitude')
    acc = data.get('accuracy')

    if lat is None or lon is None:
        return jsonify({"erro": "Latitude e longitude são obrigatórios"}), 400

    # CORREÇÃO: Usar device_id (string) e data_hora conforme modelo PosicaoGps
    # O device_id é o ID do usuário convertido para string, ou pode ser um identificador único do dispositivo
    nova_posicao = PosicaoGps(
        device_id=str(current_user.id),
        latitude=float(lat),
        longitude=float(lon),
        accuracy=float(acc) if acc is not None else None,
        data_hora=datetime.utcnow()
    )
    db.session.add(nova_posicao)
    db.session.commit()

    return jsonify({"status": "sucesso", "id": nova_posicao.id}), 201


@api_bp.route('/gps/latest', methods=['GET'])
@login_required
def gps_latest():
    """
    Retorna as últimas posições de todos os dispositivos ativos nas últimas 24 horas.
    """
    tempo_limite = datetime.utcnow() - timedelta(hours=24)

    # CORREÇÃO: Usar device_id e data_hora conforme modelo PosicaoGps
    # Subquery para pegar a última posição de cada device
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

    # CORREÇÃO: Removido p.user.nome_exibicao pois PosicaoGps não tem relação com User
    # Retornando apenas os dados disponíveis no modelo
    return jsonify([
        {
            "device_id": p.device_id,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "accuracy": p.accuracy,
            "data_hora": p.data_hora.isoformat() if p.data_hora else None
        }
        for p in ultimas_posicoes
    ])


@api_bp.route('/gps/historico/<string:device_id>', methods=['GET'])
@login_required
def historico_gps(device_id):
    """
    Retorna o histórico de posições GPS de um dispositivo.
    Parâmetros: horas (padrão 24).
    """
    horas = request.args.get('horas', 24, type=int)
    if horas <= 0 or horas > 168:  # Máximo 7 dias
        return jsonify({"erro": "Parâmetro 'horas' deve estar entre 1 e 168"}), 400

    tempo_limite = datetime.utcnow() - timedelta(hours=horas)

    # CORREÇÃO: Usar device_id (string) e data_hora conforme modelo PosicaoGps
    posicoes = PosicaoGps.query.filter(
        PosicaoGps.device_id == device_id,
        PosicaoGps.data_hora >= tempo_limite
    ).order_by(PosicaoGps.data_hora.asc()).all()

    return jsonify({
        "device_id": device_id,
        "total_pontos": len(posicoes),
        "pontos": [
            {
                "latitude": p.latitude,
                "longitude": p.longitude,
                "accuracy": p.accuracy,
                "data_hora": p.data_hora.isoformat() if p.data_hora else None
            }
            for p in posicoes
        ]
    })


# ─────────────────────────────────────────────────────────────────────────────
# TURNOS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/turnos/iniciar', methods=['POST'])
@login_required
def iniciar_turno():
    """
    Inicia um novo turno de campo para uma ação promocional.
    Corpo JSON: { acao_id, equipe_id, veiculo_id (opcional), observacoes (opcional) }
    """
    data = request.get_json() or {}
    acao_id = data.get('acao_id')
    equipe_id = data.get('equipe_id')
    veiculo_id = data.get('veiculo_id')
    observacoes = data.get('observacoes')

    if not acao_id or not equipe_id:
        return jsonify({"erro": "acao_id e equipe_id são obrigatórios"}), 400

    acao = AcaoPromocional.query.get(acao_id)
    if not acao:
        return jsonify({"erro": "Ação não encontrada"}), 404

    # Verificar permissão do usuário
    if current_user.tipo_usuario not in ['admin', 'equipe']:
        return jsonify({"erro": "Permissão negada para iniciar turno"}), 403

    turno_ativo = Turno.query.filter_by(
        acao_id=acao_id, equipe_id=equipe_id, status='ativo'
    ).first()
    if turno_ativo:
        return jsonify({
            "erro": "Já existe um turno ativo para esta equipe nesta ação",
            "turno_id": turno_ativo.id
        }), 409

    try:
        novo_turno = Turno(
            acao_id=acao_id,
            equipe_id=equipe_id,
            veiculo_id=veiculo_id,
            inicio=datetime.utcnow(),
            status='ativo',
            observacoes=observacoes
        )
        db.session.add(novo_turno)
        db.session.commit()

        return jsonify({
            "status": "sucesso",
            "turno_id": novo_turno.id,
            "inicio": novo_turno.inicio.isoformat(),
            "mensagem": "Turno iniciado com sucesso"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao iniciar turno: {str(e)}"}), 500


@api_bp.route('/turnos/<int:turno_id>/encerrar', methods=['POST'])
@login_required
def encerrar_turno(turno_id):
    """Encerra um turno ativo, registrando o horário de fim."""
    turno = Turno.query.get_or_404(turno_id)

    # Verificar permissão
    if current_user.tipo_usuario not in ['admin', 'equipe']:
        return jsonify({"erro": "Permissão negada"}), 403

    if turno.status == 'encerrado':
        return jsonify({"erro": "Turno já foi encerrado"}), 400

    data = request.get_json() or {}

    try:
        turno.fim = datetime.utcnow()
        turno.status = 'encerrado'
        if data.get('observacoes'):
            turno.observacoes = data.get('observacoes')
        db.session.commit()

        return jsonify({
            "status": "sucesso",
            "turno_id": turno.id,
            "inicio": turno.inicio.isoformat(),
            "fim": turno.fim.isoformat(),
            "duracao_minutos": turno.duracao_minutos,
            "mensagem": "Turno encerrado com sucesso"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao encerrar turno: {str(e)}"}), 500


@api_bp.route('/turnos/<int:turno_id>/pausar', methods=['POST'])
@login_required
def pausar_turno(turno_id):
    """Pausa um turno ativo temporariamente."""
    turno = Turno.query.get_or_404(turno_id)

    if current_user.tipo_usuario not in ['admin', 'equipe']:
        return jsonify({"erro": "Permissão negada"}), 403

    if turno.status != 'ativo':
        return jsonify({"erro": "Somente turnos ativos podem ser pausados"}), 400

    try:
        turno.status = 'pausado'
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Turno pausado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao pausar turno: {str(e)}"}), 500


@api_bp.route('/turnos/<int:turno_id>/retomar', methods=['POST'])
@login_required
def retomar_turno(turno_id):
    """Retoma um turno pausado."""
    turno = Turno.query.get_or_404(turno_id)

    if current_user.tipo_usuario not in ['admin', 'equipe']:
        return jsonify({"erro": "Permissão negada"}), 403

    if turno.status != 'pausado':
        return jsonify({"erro": "Somente turnos pausados podem ser retomados"}), 400

    try:
        turno.status = 'ativo'
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Turno retomado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao retomar turno: {str(e)}"}), 500


@api_bp.route('/turnos/acao/<int:acao_id>', methods=['GET'])
@login_required
def listar_turnos_acao(acao_id):
    """Lista todos os turnos de uma ação específica."""
    # Verificar acesso para clientes
    if current_user.tipo_usuario == 'cliente':
        from app.models.cliente import Cliente
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        acao = AcaoPromocional.query.get_or_404(acao_id)
        if not cliente or acao.cliente_id != cliente.id:
            return jsonify({"erro": "Acesso negado"}), 403

    turnos = Turno.query.filter_by(acao_id=acao_id).order_by(Turno.inicio.desc()).all()
    return jsonify({
        "acao_id": acao_id,
        "total": len(turnos),
        "turnos": [
            {
                "id": t.id,
                "equipe": t.equipe.nome if t.equipe else None,
                "veiculo": t.veiculo.placa if t.veiculo else None,
                "inicio": t.inicio.isoformat() if t.inicio else None,
                "fim": t.fim.isoformat() if t.fim else None,
                "status": t.status,
                "duracao_minutos": t.duracao_minutos,
                "total_fotos": len(t.fotos) if hasattr(t, 'fotos') else 0
            }
            for t in turnos
        ]
    })


# ─────────────────────────────────────────────────────────────────────────────
# ÁREAS DE ATUAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/areas/<int:acao_id>', methods=['GET'])
@login_required
def listar_areas(acao_id):
    """Retorna todas as áreas de atuação de uma ação."""
    acao = AcaoPromocional.query.get_or_404(acao_id)

    # Verificar acesso para clientes
    if current_user.tipo_usuario == 'cliente':
        from app.models.cliente import Cliente
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente or acao.cliente_id != cliente.id:
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
@login_required
def salvar_area(acao_id):
    """
    Salva uma nova área de atuação para uma ação.
    Corpo JSON: { nome, geojson, descricao (opcional), cor (opcional) }
    """
    if current_user.tipo_usuario not in ['admin', 'equipe']:
        return jsonify({"erro": "Permissão negada"}), 403

    acao = AcaoPromocional.query.get_or_404(acao_id)

    data = request.get_json() or {}
    nome = data.get('nome', 'Área Principal')
    geojson = data.get('geojson')
    descricao = data.get('descricao')
    cor = data.get('cor', '#FF9E0C')

    if not geojson:
        return jsonify({"erro": "GeoJSON é obrigatório"}), 400

    # Validar e normalizar GeoJSON
    if isinstance(geojson, dict):
        geojson_str = json.dumps(geojson)
    else:
        try:
            # Validar se é um JSON válido
            json.loads(geojson)
            geojson_str = geojson
        except (json.JSONDecodeError, TypeError):
            return jsonify({"erro": "GeoJSON inválido"}), 400

    try:
        nova_area = AreaAtuacao(
            acao_id=acao_id,
            nome=nome,
            descricao=descricao,
            geojson=geojson_str,
            cor=cor
        )
        db.session.add(nova_area)
        db.session.commit()

        return jsonify({
            "status": "sucesso",
            "area_id": nova_area.id,
            "mensagem": f"Área '{nome}' salva com sucesso"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao salvar área: {str(e)}"}), 500


@api_bp.route('/areas/item/<int:area_id>', methods=['DELETE'])
@login_required
def deletar_area(area_id):
    """Remove uma área de atuação."""
    if current_user.tipo_usuario != 'admin':
        return jsonify({"erro": "Permissão negada"}), 403

    area = AreaAtuacao.query.get_or_404(area_id)

    try:
        db.session.delete(area)
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Área removida"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao remover área: {str(e)}"}), 500


@api_bp.route("/areas/item/<int:area_id>", methods=["PUT"])
@login_required
def atualizar_area_atuacao(area_id):
    """Atualiza os dados de uma área de atuação existente."""
    if current_user.tipo_usuario not in ["admin", "equipe"]:
        return jsonify({"erro": "Permissão negada"}), 403

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
@login_required
def get_mapa_areas():
    """Retorna todas as áreas de mapa salvas."""
    areas = MapaArea.query.all()
    return jsonify([
        {
            "id": area.id,
            "nome": area.nome,
            "geojson": area.get_geojson() if hasattr(area, 'get_geojson') else area.geojson,
            "criado_em": area.criado_em.isoformat() if hasattr(area, 'criado_em') and area.criado_em else None
        }
        for area in areas
    ])


@api_bp.route("/mapa/areas", methods=["POST"])
@login_required
def post_mapa_area():
    """Recebe GeoJSON e salva uma nova área de mapa."""
    if current_user.tipo_usuario not in ["admin", "equipe"]:
        return jsonify({"erro": "Permissão negada"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    nome = data.get("nome", f"Área Desenhada {datetime.now().strftime('%Y%m%d%H%M%S')}")
    geojson_data = data.get("geojson")

    if not geojson_data:
        return jsonify({"erro": "GeoJSON é obrigatório"}), 400

    try:
        # Valida se o geojson_data é um JSON válido
        if isinstance(geojson_data, dict):
            geojson_str = json.dumps(geojson_data)
        else:
            json.loads(geojson_data)  # Tenta carregar para validar
            geojson_str = geojson_data
    except (json.JSONDecodeError, TypeError):
        return jsonify({"erro": "GeoJSON inválido"}), 400

    try:
        nova_area = MapaArea(nome=nome, geojson=geojson_str)
        db.session.add(nova_area)
        db.session.commit()

        return jsonify({"status": "sucesso", "id": nova_area.id, "mensagem": "Área salva com sucesso"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao salvar área: {str(e)}"}), 500


@api_bp.route("/mapa/areas/<int:area_id>", methods=["DELETE"])
@login_required
def delete_mapa_area(area_id):
    """Remove uma área de mapa pelo ID."""
    if current_user.tipo_usuario not in ["admin", "equipe"]:
        return jsonify({"erro": "Permissão negada"}), 403

    area = MapaArea.query.get_or_404(area_id)

    try:
        db.session.delete(area)
        db.session.commit()
        return jsonify({"status": "sucesso", "mensagem": "Área removida com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao remover área: {str(e)}"}), 500


@api_bp.route("/mapa/areas/<int:area_id>", methods=["PUT"])
@login_required
def update_mapa_area(area_id):
    """Atualiza uma área de mapa existente."""
    if current_user.tipo_usuario not in ["admin", "equipe"]:
        return jsonify({"erro": "Permissão negada"}), 403

    area = MapaArea.query.get_or_404(area_id)
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    try:
        if "nome" in data:
            area.nome = data["nome"]
        if "geojson" in data:
            geojson_data = data["geojson"]
            try:
                if isinstance(geojson_data, dict):
                    area.geojson = json.dumps(geojson_data)
                else:
                    json.loads(geojson_data)
                    area.geojson = geojson_data
            except (json.JSONDecodeError, TypeError):
                return jsonify({"erro": "GeoJSON inválido"}), 400

        db.session.commit()
        return jsonify({"status": "sucesso", "id": area.id, "mensagem": "Área atualizada com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar área: {str(e)}"}), 500


@api_bp.route('/areas/verificar', methods=['POST'])
@login_required
def verificar_ponto_na_area():
    """
    Verifica se um ponto GPS está dentro de alguma área de atuação.
    Corpo JSON: { acao_id, latitude, longitude }
    """
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
@login_required
def enviar_foto():
    """
    Recebe uma foto com geolocalização e a associa a um turno.
    Verifica se a foto está dentro da área de atuação da ação.
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

    # Verificar permissão do usuário
    if current_user.tipo_usuario not in ['admin', 'equipe']:
        return jsonify({"erro": "Permissão negada"}), 403

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
            url=foto_url,
            latitude=lat,
            longitude=lon,
            descricao=descricao,
            dentro_da_area=dentro_da_area,
            data_hora=datetime.utcnow()
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
@login_required
def fotos_do_turno(turno_id):
    """Retorna todas as fotos de um turno específico."""
    turno = Turno.query.get_or_404(turno_id)

    # Verificar acesso para clientes
    if current_user.tipo_usuario == 'cliente':
        from app.models.cliente import Cliente
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente or turno.acao.cliente_id != cliente.id:
            return jsonify({"erro": "Acesso negado"}), 403

    fotos = FotoAuditoria.query.filter_by(turno_id=turno_id).order_by(
        FotoAuditoria.data_hora.asc()
    ).all()

    return jsonify({
        "turno_id": turno_id,
        "total_fotos": len(fotos),
        "fotos": [
            {
                "id": f.id,
                "url": f.url,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "descricao": f.descricao,
                "dentro_da_area": f.dentro_da_area,
                "data_hora": f.data_hora.isoformat() if f.data_hora else None
            }
            for f in fotos
        ]
    })


# ─────────────────────────────────────────────────────────────────────────────
# MAPA (dados consolidados para o Leaflet)
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/mapa/dados')
@login_required
def mapa_dados():
    """
    Retorna dados JSON consolidados para o mapa Leaflet.
    Inclui rastros GPS, fotos geolocalizadas, áreas de atuação e veículos.
    Filtra por acao_id se fornecido via query string.
    """
    tempo_limite = datetime.utcnow() - timedelta(hours=24)
    acao_id = request.args.get('acao_id', type=int)

    # Verificar permissões do cliente
    if current_user.tipo_usuario == 'cliente':
        from app.models.cliente import Cliente
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente:
            return jsonify({"veiculos": [], "fotos": [], "rastros_gps": {}, "areas": [], "auditorias_legadas": []})
        filtro_acoes = [a.id for a in AcaoPromocional.query.filter_by(cliente_id=cliente.id).all()]
    else:
        filtro_acoes = None

    # Fotos novas (FotoAuditoria via Turnos)
    fotos_query = FotoAuditoria.query.join(Turno)
    if acao_id:
        fotos_query = fotos_query.filter(Turno.acao_id == acao_id)
    elif filtro_acoes is not None:
        fotos_query = fotos_query.filter(Turno.acao_id.in_(filtro_acoes))
    else:
        fotos_query = fotos_query.filter(FotoAuditoria.data_hora >= tempo_limite)
    fotos = fotos_query.all()

    # Fotos legadas (Auditoria)
    aud_query = Auditoria.query
    if acao_id:
        aud_query = aud_query.filter_by(acao_id=acao_id)
    elif filtro_acoes is not None:
        aud_query = aud_query.filter(Auditoria.acao_id.in_(filtro_acoes))
    else:
        aud_query = aud_query.filter(Auditoria.data_hora >= tempo_limite)
    auditorias_legadas = aud_query.all()

    # Rastros GPS
    rastros_gps = {}
    if current_user.tipo_usuario != 'cliente':
        posicoes = PosicaoGps.query.filter(
            PosicaoGps.data_hora >= tempo_limite
        ).order_by(PosicaoGps.data_hora.asc()).all()
        for p in posicoes:
            key = str(p.device_id)
            if key not in rastros_gps:
                rastros_gps[key] = []
            rastros_gps[key].append([p.latitude, p.longitude])

    veiculos = []
    if current_user.tipo_usuario != 'cliente':
        veiculos = Veiculo.query.all()

    areas_query = AreaAtuacao.query
    if acao_id:
        areas_query = areas_query.filter_by(acao_id=acao_id)
    elif filtro_acoes is not None:
        areas_query = areas_query.filter(AreaAtuacao.acao_id.in_(filtro_acoes))
    areas = areas_query.all()

    return jsonify({
        "veiculos": [
            {"id": v.id, "placa": v.placa, "modelo": v.modelo, "status": v.status}
            for v in veiculos
        ],
        "fotos": [
            {
                "id": f.id,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "url": f.url,
                "descricao": f.descricao,
                "dentro_da_area": f.dentro_da_area,
                "data_hora": f.data_hora.isoformat() if f.data_hora else None,
                "turno_id": f.turno_id
            }
            for f in fotos
        ],
        "auditorias_legadas": [
            {
                "id": a.id,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "foto_url": a.foto_url,
                "descricao": a.descricao,
                "acao": a.acao.local_alvo if a.acao else ""
            }
            for a in auditorias_legadas
        ],
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
        ]
    })


@api_bp.route('/mapa/dados/acao/<int:acao_id>')
@login_required
def mapa_dados_acao(acao_id):
    """
    Retorna dados completos do mapa para uma ação específica.
    Inclui turnos, rastros GPS, fotos e áreas.
    """
    acao = AcaoPromocional.query.get_or_404(acao_id)

    # Verificar acesso para clientes
    if current_user.tipo_usuario == 'cliente':
        from app.models.cliente import Cliente
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        if not cliente or acao.cliente_id != cliente.id:
            return jsonify({"erro": "Acesso negado"}), 403

    turnos = Turno.query.filter_by(acao_id=acao_id).all()
    areas = AreaAtuacao.query.filter_by(acao_id=acao_id).all()
    fotos = FotoAuditoria.query.join(Turno).filter(Turno.acao_id == acao_id).all()

    # CORREÇÃO CRÍTICA: Lógica de rastros GPS por turno
    # Buscar os usuários da equipe do turno, não qualquer usuário com device_id
    rastros_por_turno = {}
    from app.models.user import User
    from app.models.equipe import Equipe

    for turno in turnos:
        if not turno.inicio:
            continue

        # Buscar membros da equipe deste turno que têm device_id
        equipe = turno.equipe
        if not equipe:
            continue

        # Buscar usuários membros desta equipe com device_id configurado
        # Assumindo que há uma relação entre Equipe e User, ou que User tem equipe_id
        membros_com_device = User.query.filter(
            User.equipe_id == equipe.id,
            User.device_id.isnot(None)
        ).all()

        pontos_turno = []
        for usuario in membros_com_device:
            fim = turno.fim or datetime.utcnow()
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
            "local_alvo": acao.local_alvo,
            "bairro": acao.bairro,
            "cidade": acao.cidade,
            "data": acao.data.isoformat() if acao.data else None,
            "status": acao.status,
            "cliente": acao.cliente.nome_empresa if acao.cliente else None
        },
        "turnos": [
            {
                "id": t.id,
                "equipe": t.equipe.nome if t.equipe else None,
                "veiculo": t.veiculo.placa if t.veiculo else None,
                "inicio": t.inicio.isoformat() if t.inicio else None,
                "fim": t.fim.isoformat() if t.fim else None,
                "status": t.status,
                "duracao_minutos": t.duracao_minutos
            }
            for t in turnos
        ],
        "rastros_por_turno": rastros_por_turno,
        "fotos": [
            {
                "id": f.id,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "url": f.url,
                "descricao": f.descricao,
                "dentro_da_area": f.dentro_da_area,
                "data_hora": f.data_hora.isoformat() if f.data_hora else None,
                "turno_id": f.turno_id
            }
            for f in fotos
        ],
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