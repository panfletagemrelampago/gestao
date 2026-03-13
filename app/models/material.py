from datetime import datetime
from app.extensions import db

class Material(db.Model):
    __tablename__ = 'materiais'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer)
    data_inicio = db.Column(db.Date)
    data_termino = db.Column(db.Date)
    nome_campanha = db.Column(db.String(100))
    responsavel = db.Column(db.String(100))
    documento_url = db.Column(db.String(500))
    imagem_url = db.Column(db.String(500))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Material {self.nome_campanha} - {self.empresa}>'
