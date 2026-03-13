from datetime import datetime
from app.extensions import db

class Vaga(db.Model):
    __tablename__ = 'vagas'
    
    id = db.Column(db.Integer, primary_key=True)
    dados_pessoais = db.Column(db.JSON)
    dados_contato = db.Column(db.JSON)
    dados_profissionais = db.Column(db.JSON)
    dados_bancarios = db.Column(db.JSON)
    arquivos = db.Column(db.JSON) # Armazena URLs do Cloudinary
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vaga {self.id} - {self.data_cadastro}>'
