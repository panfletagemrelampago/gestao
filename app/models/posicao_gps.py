from datetime import datetime
from app.extensions import db

class PosicaoGps(db.Model):
    __tablename__ = 'posicoes_gps'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    velocidade = db.Column(db.Float, default=0.0) # Em km/h
    bateria = db.Column(db.Float, nullable=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<PosicaoGps {self.device_id} - {self.data_hora}>'
