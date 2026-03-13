from datetime import datetime
from app.extensions import db

class MovimentacaoMaterial(db.Model):
    __tablename__ = 'movimentacoes_materiais'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materiais.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    tipo_movimento = db.Column(db.Enum('entrada', 'saida', name='mov_types'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_movimento = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MovimentacaoMaterial {self.id} - {self.tipo_movimento}>'
