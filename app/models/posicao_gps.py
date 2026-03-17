from datetime import datetime
from app.extensions import db


class PosicaoGps(db.Model):
    __tablename__ = 'posicoes_gps'

    id = db.Column(db.Integer, primary_key=True)

    # Identificação do dispositivo
    device_id = db.Column(db.Integer, nullable=False, index=True)

    # Coordenadas GPS
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # 🔥 CORREÇÃO PRINCIPAL (evita o erro do Render)
    accuracy = db.Column(db.Float, nullable=True)

    # Dados adicionais
    velocidade = db.Column(db.Float, default=0.0)  # km/h
    bateria = db.Column(db.Float, nullable=True)

    # Data/hora do registro
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<PosicaoGps {self.device_id} - {self.data_hora}>'