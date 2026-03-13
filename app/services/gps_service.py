import math
from app.models.posicao_gps import PosicaoGps
from app.extensions import db

class GpsService:
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """Calcula a distância entre dois pontos em metros."""
        R = 6371000  # Raio da Terra em metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def process_and_save_position(device_id, latitude, longitude, speed_knots, battery, fix_time):
        """
        Processa dados brutos do GPS, aplica filtro de ruído e salva se necessário.
        """
        # Converter velocidade de nós para km/h (1 nó = 1.852 km/h)
        speed_kmh = speed_knots * 1.852

        # Buscar última posição salva para este dispositivo
        last_pos = PosicaoGps.query.filter_by(device_id=device_id).order_by(PosicaoGps.data_hora.desc()).first()

        if last_pos:
            distance = GpsService.haversine(last_pos.latitude, last_pos.longitude, latitude, longitude)
            
            # Filtro de ruído (Drift):
            # Se a distância < 5m e a velocidade for baixa, não salvar novo ponto.
            if distance < 5 and speed_kmh < 1:
                return None

        # Criar e salvar novo ponto
        new_pos = PosicaoGps(
            device_id=device_id,
            latitude=latitude,
            longitude=longitude,
            velocidade=speed_kmh,
            bateria=battery,
            data_hora=fix_time
        )
        db.session.add(new_pos)
        db.session.commit()
        return new_pos
