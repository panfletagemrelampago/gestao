import json
from datetime import datetime
from app.extensions import db

class MapaArea(db.Model):
    __tablename__ = 'mapa_areas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, default=f"Área de {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    geojson = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def get_geojson(self):
        try:
            return json.loads(self.geojson)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_geojson(self, geojson_data):
        self.geojson = json.dumps(geojson_data)

    def __repr__(self):
        return f'<MapaArea {self.nome} - ID {self.id}>'
