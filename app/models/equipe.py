from datetime import datetime
from app.extensions import db

class Equipe(db.Model):
    __tablename__ = 'equipes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    foto = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    veiculos = db.relationship('Veiculo', backref='motorista', lazy=True)

    def __repr__(self):
        return f'<Equipe {self.nome}>'
