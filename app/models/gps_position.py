from datetime import datetime
from app.extensions import db

class GpsPosition(db.Model):
    __tablename__ = 'gps_positions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relacionamento com o usuário
    user = db.relationship('User', backref=db.backref('gps_positions', lazy=True))

    def __repr__(self):
        return f'<GpsPosition {self.user_id} - {self.created_at}>'
