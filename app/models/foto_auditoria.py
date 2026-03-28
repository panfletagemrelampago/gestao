"""
Model FotoAuditoria: representa uma foto tirada durante a execução de um turno
de campo. Cada foto possui geolocalização e é vinculada a um turno específico,
permitindo exibição no mapa e comprovação da cobertura da área.

Campos de ownership:
- usuario_id: ID do usuário que registrou a foto (para filtro por funcionário)
- cliente_id: ID do cliente associado à ação (para filtro por cliente)
- acao_id:    ID da ação promocional (fonte de verdade, substitui auditoria_id legado)

REFATORAÇÃO (Passo 1):
- Removido campo auditoria_id (ponte legada para tabela auditorias)
- Adicionado acao_id como FK direta para acoes_promocionais
- data_hora padronizado para UTC puro (datetime.utcnow); conversão de fuso
  ocorre exclusivamente na camada de exibição (templates/serializers)
"""

from datetime import datetime, timezone
from app.extensions import db


def _utcnow():
    """Retorna datetime UTC naive (sem tzinfo) para persistência uniforme no PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FotoAuditoria(db.Model):
    __tablename__ = 'fotos_auditoria'

    id = db.Column(db.Integer, primary_key=True)

    # Vínculo principal: turno de campo
    turno_id = db.Column(
        db.Integer,
        db.ForeignKey('turnos.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )

    # Vínculo direto com a ação (substitui auditoria_id legado)
    acao_id = db.Column(
        db.Integer,
        db.ForeignKey('acoes_promocionais.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # OWNERSHIP: usuário que registrou a foto
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True,
        index=True
    )

    # OWNERSHIP: cliente associado à ação da foto
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id'),
        nullable=True,
        index=True
    )

    # URL da imagem (Cloudinary)
    url = db.Column(
        db.String(500),
        nullable=False
    )

    # Geolocalização
    latitude = db.Column(
        db.Float,
        nullable=False,
        index=True
    )

    longitude = db.Column(
        db.Float,
        nullable=False,
        index=True
    )

    descricao = db.Column(
        db.Text,
        nullable=True
    )

    dentro_da_area = db.Column(
        db.Boolean,
        default=None,
        nullable=True
    )

    # Armazenado sempre em UTC naive; conversão de fuso na camada de exibição
    data_hora = db.Column(
        db.DateTime,
        default=_utcnow,
        index=True
    )

    # Relacionamentos
    acao = db.relationship('AcaoPromocional', backref='fotos', lazy=True)
    usuario = db.relationship('User', backref='fotos_auditoria', lazy=True)

    def __repr__(self):
        return f'<FotoAuditoria {self.id} - Turno {self.turno_id} - User {self.usuario_id}>'

    def to_dict(self):
        """Serialização básica compatível com o mapa Leaflet."""
        return {
            "id": self.id,
            "lat": self.latitude,
            "lng": self.longitude,
            "img": self.url,
            "descricao": self.descricao,
            "turno_id": self.turno_id,
            "acao_id": self.acao_id,
            "usuario_id": self.usuario_id,
            "cliente_id": self.cliente_id,
            "data": self.data_hora.isoformat() if self.data_hora else None
        }
