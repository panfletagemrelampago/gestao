from datetime import datetime
from app.extensions import db

class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    cor = db.Column(db.String(20), nullable=False)
    motorista_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=True)
    status = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Veiculo {self.placa}>'
