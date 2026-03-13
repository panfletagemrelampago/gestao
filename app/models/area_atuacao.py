"""
Model AreaAtuacao: representa a região geográfica delimitada para uma ação
promocional. Armazena o polígono como GeoJSON, permitindo verificar cobertura
e exibir a área no mapa Leaflet.
"""
import json
import math
from datetime import datetime
from app.extensions import db


class AreaAtuacao(db.Model):
    __tablename__ = 'areas_atuacao'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(
        db.Integer,
        db.ForeignKey('acoes_promocionais.id'),
        nullable=False,
        index=True
    )
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    geojson = db.Column(db.Text, nullable=False)  # Armazena o GeoJSON como string
    cor = db.Column(db.String(10), default='#FF9E0C')  # Cor de exibição no mapa
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relacionamento
    acao = db.relationship('AcaoPromocional', backref='areas', lazy=True)

    def get_geojson(self):
        """Retorna o GeoJSON como dicionário Python."""
        try:
            return json.loads(self.geojson)
        except (json.JSONDecodeError, TypeError):
            return None

    def ponto_dentro_da_area(self, latitude, longitude):
        """
        Verifica se um ponto (lat, lon) está dentro do polígono usando o
        algoritmo Ray-Casting. Suporta GeoJSON do tipo Polygon e Feature.
        Retorna True se o ponto estiver dentro, False caso contrário.
        """
        geojson_data = self.get_geojson()
        if not geojson_data:
            return False

        # Extrair as coordenadas do polígono
        coordinates = None
        geo_type = geojson_data.get('type')

        if geo_type == 'Feature':
            geometry = geojson_data.get('geometry', {})
            if geometry.get('type') == 'Polygon':
                coordinates = geometry.get('coordinates', [[]])[0]
        elif geo_type == 'Polygon':
            coordinates = geojson_data.get('coordinates', [[]])[0]
        elif geo_type == 'FeatureCollection':
            features = geojson_data.get('features', [])
            if features:
                first = features[0]
                geom = first.get('geometry', {})
                if geom.get('type') == 'Polygon':
                    coordinates = geom.get('coordinates', [[]])[0]

        if not coordinates:
            return False

        # Ray-Casting: GeoJSON usa [longitude, latitude]
        x, y = longitude, latitude
        n = len(coordinates)
        inside = False
        j = n - 1

        for i in range(n):
            xi, yi = coordinates[i][0], coordinates[i][1]
            xj, yj = coordinates[j][0], coordinates[j][1]
            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi
            )
            if intersect:
                inside = not inside
            j = i

        return inside

    def __repr__(self):
        return f'<AreaAtuacao {self.nome} - Acao {self.acao_id}>'
