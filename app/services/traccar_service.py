import requests
from flask import current_app

class TraccarService:
    @staticmethod
    def get_positions(device_id=None):
        url = f"{current_app.config['TRACCAR_URL']}/api/positions"
        params = {}
        if device_id:
            params['deviceId'] = device_id
        
        try:
            response = requests.get(
                url, 
                auth=(current_app.config['TRACCAR_USER'], current_app.config['TRACCAR_PASSWORD']),
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar posições do Traccar: {e}")
            return []

    @staticmethod
    def get_devices():
        url = f"{current_app.config['TRACCAR_URL']}/api/devices"
        try:
            response = requests.get(
                url, 
                auth=(current_app.config['TRACCAR_USER'], current_app.config['TRACCAR_PASSWORD']),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar dispositivos do Traccar: {e}")
            return []
