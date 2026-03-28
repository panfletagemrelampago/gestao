"""
GpsService: camada de serviço para processamento e persistência de posições GPS.

REFATORAÇÃO (Passo 2):
- Adicionada validação de 'deslocamento improvável' (impossible jump):
  calcula a velocidade implícita entre o ponto anterior e o novo ponto;
  se exceder MAX_SPEED_KMH (padrão 200 km/h), o ponto é descartado.
- Filtro de ruído (drift < 5 m + velocidade < 1 km/h) mantido.
- data_hora persistida em UTC naive (_utcnow) para consistência com o restante
  da aplicação após padronização do Passo 1.
- Toda a lógica de coordenadas permanece centralizada aqui; rotas não devem
  duplicar nenhuma dessas regras.
"""

import math
from datetime import datetime, timezone
from app.models.posicao_gps import PosicaoGps
from app.extensions import db


# Velocidade máxima plausível para um veículo de campo (km/h).
# Pontos que implicariam velocidade acima deste limite são descartados.
MAX_SPEED_KMH = 200.0

# Distância mínima de movimento para registrar novo ponto (metros).
MIN_DISTANCE_M = 5.0

# Velocidade mínima para registrar novo ponto mesmo com distância baixa (km/h).
MIN_SPEED_KMH = 1.0


def _utcnow():
    """Retorna datetime UTC naive para persistência uniforme no PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class GpsService:

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula a distância em metros entre dois pontos geográficos
        usando a fórmula de Haversine.
        """
        R = 6_371_000  # Raio médio da Terra em metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def process_and_save_position(
        device_id: int,
        latitude: float,
        longitude: float,
        speed_knots: float,
        battery: float,
        fix_time: datetime,
    ):
        """
        Processa dados brutos do GPS, aplica filtros e persiste se necessário.

        Filtros aplicados (em ordem):
        1. Filtro de ruído (drift): descarta se distância < MIN_DISTANCE_M
           e velocidade < MIN_SPEED_KMH.
        2. Filtro de deslocamento improvável (impossible jump): descarta se a
           velocidade implícita entre o ponto anterior e o novo ponto exceder
           MAX_SPEED_KMH.

        Parâmetros:
            device_id    – ID inteiro do dispositivo/usuário.
            latitude     – Latitude em graus decimais.
            longitude    – Longitude em graus decimais.
            speed_knots  – Velocidade reportada pelo GPS em nós.
            battery      – Nível de bateria (0–100 ou None).
            fix_time     – datetime UTC do fix GPS (naive ou aware).

        Retorna a instância PosicaoGps salva, ou None se descartado.
        """
        # Normalizar fix_time para naive UTC
        if fix_time is None:
            fix_time = _utcnow()
        elif fix_time.tzinfo is not None:
            fix_time = fix_time.astimezone(timezone.utc).replace(tzinfo=None)

        # Converter velocidade de nós para km/h (1 nó = 1.852 km/h)
        speed_kmh = speed_knots * 1.852

        # Buscar última posição salva para este dispositivo
        last_pos = (
            PosicaoGps.query
            .filter_by(device_id=device_id)
            .order_by(PosicaoGps.data_hora.desc())
            .first()
        )

        if last_pos:
            distance_m = GpsService.haversine(
                last_pos.latitude, last_pos.longitude, latitude, longitude
            )

            # ── Filtro 1: ruído / drift ──────────────────────────────────────
            if distance_m < MIN_DISTANCE_M and speed_kmh < MIN_SPEED_KMH:
                return None

            # ── Filtro 2: deslocamento improvável ────────────────────────────
            # Calcula a velocidade implícita entre o último ponto e o novo.
            last_dt = last_pos.data_hora
            if last_dt.tzinfo is not None:
                last_dt = last_dt.replace(tzinfo=None)

            elapsed_seconds = (fix_time - last_dt).total_seconds()

            if elapsed_seconds > 0:
                implied_speed_kmh = (distance_m / 1000.0) / (elapsed_seconds / 3600.0)
                if implied_speed_kmh > MAX_SPEED_KMH:
                    return None  # Descarta ponto impossível

        # Persistir novo ponto
        new_pos = PosicaoGps(
            device_id=device_id,
            latitude=latitude,
            longitude=longitude,
            velocidade=speed_kmh,
            bateria=battery,
            data_hora=fix_time,
        )
        db.session.add(new_pos)
        db.session.commit()
        return new_pos
