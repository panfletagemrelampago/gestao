"""
Schemas Marshmallow para serialização/deserialização das respostas da API REST.

REFATORAÇÃO (Passo 2):
- Substitui a montagem manual de dicionários JSON nas rotas da API.
- Padroniza os campos expostos e seus tipos em um único lugar.
- Conversão de fuso (UTC → GMT-4) para campos de exibição feita via
  método @post_dump quando necessário.

Instalação: marshmallow já é dependência do flask-marshmallow; instalar com
    pip install marshmallow flask-marshmallow
"""

from marshmallow import Schema, fields, post_dump
from datetime import timezone, timedelta


GMT_MINUS_4 = timezone(timedelta(hours=-4))


def _to_local(dt_iso: str | None) -> str | None:
    """Converte string ISO UTC para ISO GMT-4 (para uso em @post_dump)."""
    if dt_iso is None:
        return None
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(dt_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(GMT_MINUS_4).isoformat()
    except ValueError:
        return dt_iso


# ─────────────────────────────────────────────────────────────────────────────
# PosicaoGps
# ─────────────────────────────────────────────────────────────────────────────

class PosicaoGpsSchema(Schema):
    """Serializa uma posição GPS para as respostas da API."""
    id = fields.Int(dump_only=True)
    device_id = fields.Int()
    latitude = fields.Float()
    longitude = fields.Float()
    accuracy = fields.Float(allow_none=True)
    velocidade = fields.Float()
    bateria = fields.Float(allow_none=True)
    data_hora = fields.DateTime(format='iso', dump_only=True)


class PosicaoGpsResumoSchema(Schema):
    """Versão compacta para listagens de mapa (lat/lng apenas)."""
    device_id = fields.Int()
    latitude = fields.Float()
    longitude = fields.Float()
    accuracy = fields.Float(allow_none=True)
    data_hora = fields.DateTime(format='iso', dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# FotoAuditoria
# ─────────────────────────────────────────────────────────────────────────────

class FotoAuditoriaSchema(Schema):
    """Serializa uma foto de campo para as respostas da API."""
    id = fields.Int(dump_only=True)
    turno_id = fields.Int(allow_none=True)
    acao_id = fields.Int(allow_none=True)
    usuario_id = fields.Int(allow_none=True)
    cliente_id = fields.Int(allow_none=True)
    url = fields.Str()
    latitude = fields.Float()
    longitude = fields.Float()
    descricao = fields.Str(allow_none=True)
    dentro_da_area = fields.Bool(allow_none=True)
    data_hora = fields.DateTime(format='iso', dump_only=True)


class FotoAuditoriaMapaSchema(Schema):
    """Versão compacta para o mapa Leaflet (compatível com to_dict legado)."""
    id = fields.Int(dump_only=True)
    lat = fields.Float(attribute='latitude')
    lng = fields.Float(attribute='longitude')
    img = fields.Str(attribute='url')
    descricao = fields.Str(allow_none=True)
    turno_id = fields.Int(allow_none=True)
    acao_id = fields.Int(allow_none=True)
    usuario_id = fields.Int(allow_none=True)
    cliente_id = fields.Int(allow_none=True)
    data = fields.DateTime(format='iso', attribute='data_hora', dump_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# Turno
# ─────────────────────────────────────────────────────────────────────────────

class TurnoSchema(Schema):
    """Serializa um turno de campo para as respostas da API."""
    id = fields.Int(dump_only=True)
    acao_id = fields.Int()
    equipe_nome = fields.Method('get_equipe_nome')
    veiculo_placa = fields.Method('get_veiculo_placa')
    inicio = fields.DateTime(format='iso', dump_only=True)
    fim = fields.DateTime(format='iso', allow_none=True, dump_only=True)
    status = fields.Str()
    duracao_minutos = fields.Int(dump_only=True)
    total_fotos = fields.Method('get_total_fotos')

    def get_equipe_nome(self, obj):
        return obj.equipe.nome if obj.equipe else None

    def get_veiculo_placa(self, obj):
        return obj.veiculo.placa if obj.veiculo else None

    def get_total_fotos(self, obj):
        return len(obj.fotos) if hasattr(obj, 'fotos') else 0


# ─────────────────────────────────────────────────────────────────────────────
# Instâncias reutilizáveis (singleton por schema)
# ─────────────────────────────────────────────────────────────────────────────

posicao_gps_schema = PosicaoGpsSchema()
posicoes_gps_schema = PosicaoGpsSchema(many=True)
posicao_gps_resumo_schema = PosicaoGpsResumoSchema()
posicoes_gps_resumo_schema = PosicaoGpsResumoSchema(many=True)

foto_auditoria_schema = FotoAuditoriaSchema()
fotos_auditoria_schema = FotoAuditoriaSchema(many=True)
foto_mapa_schema = FotoAuditoriaMapaSchema()
fotos_mapa_schema = FotoAuditoriaMapaSchema(many=True)

turno_schema = TurnoSchema()
turnos_schema = TurnoSchema(many=True)
