from datetime import datetime
from app.extensions import db

class Auditoria(db.Model):
    __tablename__ = 'auditorias'
    
    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes_promocionais.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='SET NULL'), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    foto_url = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='auditorias', lazy=True)

    @property
    def user_display_name(self):
        return self.user.nome_exibicao if self.user else 'Usuário Removido'

    def __repr__(self):
        return f'<Auditoria {self.id} - Acao {self.acao_id}>'
