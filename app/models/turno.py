"""
Model Turno: representa um período de trabalho de campo vinculado a uma ação
promocional, equipe e veículo. Registra início, fim e status do turno.
"""
from datetime import datetime
from app.extensions import db


class Turno(db.Model):
    __tablename__ = 'turnos'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(
        db.Integer,
        db.ForeignKey('acoes_promocionais.id'),
        nullable=False,
        index=True
    )
    equipe_id = db.Column(
        db.Integer,
        db.ForeignKey('equipes.id'),
        nullable=True,
        index=True
    )
    veiculo_id = db.Column(
        db.Integer,
        db.ForeignKey('veiculos.id'),
        nullable=True
    )
    inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fim = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default='ativo'
    )
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    acao = db.relationship('AcaoPromocional', backref='turnos', lazy=True)
    equipe = db.relationship('Equipe', backref='turnos', lazy=True)
    veiculo = db.relationship('Veiculo', backref='turnos', lazy=True)
    fotos = db.relationship('FotoAuditoria', backref='turno', lazy=True, cascade='all, delete-orphan')

    @property
    def duracao_minutos(self):
        """Calcula a duração do turno em minutos."""
        if self.inicio and self.fim:
            delta = self.fim - self.inicio
            return int(delta.total_seconds() / 60)
        return None

    def __repr__(self):
        return f'<Turno {self.id} - Acao {self.acao_id} - {self.status}>'
