from datetime import datetime
from app.extensions import db

class Auditoria(db.Model):
    __tablename__ = 'auditorias'
    
    id = db.Column(db.Integer, primary_key=True)

    # 🔥 AGORA VINCULADO AO TURNO (CORREÇÃO PRINCIPAL)
    turno_id = db.Column(
        db.Integer,
        db.ForeignKey('turnos.id'),
        nullable=False,
        index=True
    )

    # (OPCIONAL, mas recomendado manter)
    acao_id = db.Column(
        db.Integer,
        db.ForeignKey('acoes_promocionais.id'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    descricao = db.Column(db.Text, nullable=True)

    foto_url = db.Column(
        db.String(255),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    data_hora = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # 🔗 RELACIONAMENTO COM TURNO
    turno = db.relationship(
        'Turno',
        backref=db.backref('auditorias', lazy=True)
    )

    def __repr__(self):
        return f'<Auditoria {self.id} - Turno {self.turno_id}>'
