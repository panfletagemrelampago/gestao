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
    turno_id = db.Column(
        db.Integer,
        db.ForeignKey('turnos.id'),
        nullable=False,
        index=True
    )
    # Mantém compatibilidade com o model Auditoria legado (opcional)
    auditoria_id = db.Column(
        db.Integer,
        db.ForeignKey('auditorias.id'),
        nullable=True
    )
    url = db.Column(db.String(500), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    dentro_da_area = db.Column(db.Boolean, default=None, nullable=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<FotoAuditoria {self.id} - Turno {self.turno_id}>'
