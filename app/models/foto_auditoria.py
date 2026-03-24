"""
Model FotoAuditoria: representa uma foto tirada durante a execução de um turno
de campo. Cada foto possui geolocalização e é vinculada a um turno específico,
permitindo exibição no mapa e comprovação da cobertura da área.

Campos de ownership adicionados:
- usuario_id: ID do usuário que registrou a foto (para filtro por funcionário)
- cliente_id: ID do cliente associado à ação (para filtro por cliente)
"""

from datetime import datetime
from app.extensions import db


class FotoAuditoria(db.Model):
    __tablename__ = 'fotos_auditoria'

    id = db.Column(db.Integer, primary_key=True)

    # 🔥 AGORA OPCIONAL (pra não quebrar seu fluxo atual)
    turno_id = db.Column(
        db.Integer,
        db.ForeignKey('turnos.id'),
        nullable=True,
        index=True
    )

    # Compatibilidade com Auditoria
    auditoria_id = db.Column(
        db.Integer,
        db.ForeignKey('auditorias.id'),
        nullable=True,
        index=True
    )

    # 🔐 OWNERSHIP: usuário que registrou a foto
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True,
        index=True
    )

    # 🔐 OWNERSHIP: cliente associado à ação da foto
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id'),
        nullable=True,
        index=True
    )

    # URL da imagem
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

    data_hora = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )

    def __repr__(self):
        return f'<FotoAuditoria {self.id} - Turno {self.turno_id} - User {self.usuario_id}>'

    # 🔥 PADRÃO COMPATÍVEL COM SEU MAPA
    def to_dict(self):
        return {
            "id": self.id,
            "lat": self.latitude,
            "lng": self.longitude,
            "img": self.url,
            "descricao": self.descricao,
            "turno_id": self.turno_id,
            "usuario_id": self.usuario_id,
            "cliente_id": self.cliente_id,
            "data": self.data_hora.isoformat() if self.data_hora else None
        }
