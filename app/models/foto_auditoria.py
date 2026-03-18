"""
Model FotoAuditoria: representa uma foto tirada durante a execução de um turno
de campo. Cada foto possui geolocalização e é vinculada a um turno específico,
permitindo exibição no mapa e comprovação da cobertura da área.
"""

from datetime import datetime
from app.extensions import db


class FotoAuditoria(db.Model):
    __tablename__ = 'fotos_auditoria'

    id = db.Column(db.Integer, primary_key=True)

    # Relacionamento com Turno (OBRIGATÓRIO)
    turno_id = db.Column(
        db.Integer,
        db.ForeignKey('turnos.id'),
        nullable=False,
        index=True
    )

    # Compatibilidade com Auditoria (LEGADO - opcional)
    auditoria_id = db.Column(
        db.Integer,
        db.ForeignKey('auditorias.id'),
        nullable=True,
        index=True
    )

    # URL da imagem (Cloudinary ou armazenamento local)
    url = db.Column(
        db.String(500),
        nullable=False
    )

    # Geolocalização (ESSENCIAL)
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

    # Informações adicionais
    descricao = db.Column(
        db.Text,
        nullable=True
    )

    # Validação de área (opcional para futuras regras)
    dentro_da_area = db.Column(
        db.Boolean,
        default=None,
        nullable=True
    )

    # Data/hora da captura
    data_hora = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )

    # ============================================
    # REPRESENTAÇÃO
    # ============================================
    def __repr__(self):
        return f'<FotoAuditoria {self.id} - Turno {self.turno_id}>'

    # ============================================
    # SERIALIZAÇÃO (PADRÃO MAPA NOVO)
    # ============================================
    def to_dict(self):
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "url": self.url,
            "descricao": self.descricao,
            "turno_id": self.turno_id,
            "auditoria_id": self.auditoria_id,
            "dentro_da_area": self.dentro_da_area,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None
        }