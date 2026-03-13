from datetime import datetime
from app.extensions import db

class AcaoPromocional(db.Model):
    __tablename__ = 'acoes_promocionais'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    local_alvo = db.Column(db.String(100), nullable=False)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    tipo_servico = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    turno = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), default='Planejada')
    lider_equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    # Relacionamentos
    auditorias = db.relationship('Auditoria', backref='acao', lazy=True)

    def __repr__(self):
        return f'<AcaoPromocional {self.local_alvo} - {self.data}>'
