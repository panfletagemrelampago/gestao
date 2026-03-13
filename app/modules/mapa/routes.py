from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.cliente import Cliente
import requests
import os

mapa_bp = Blueprint('mapa', __name__)

@mapa_bp.route('/')
@login_required
def index():
    # Lógica de Filtro de Ações (Original)
    if current_user.tipo_usuario == 'cliente':
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        acoes = AcaoPromocional.query.filter_by(cliente_id=cliente.id).all() if cliente else []
    elif current_user.tipo_usuario == 'equipe':
        acoes = AcaoPromocional.query.filter_by(lider_equipe_id=current_user.id).all()
    else:
        acoes = AcaoPromocional.query.order_by(AcaoPromocional.data.desc()).all()

    # --- INTEGRAÇÃO TRACCAR ---
    posicoes_traccar = []
    # Pega as credenciais das variáveis de ambiente do Render
    traccar_user = os.environ.get('TRACCAR_USER')
    traccar_pass = os.environ.get('TRACCAR_PASS')
    traccar_url = os.environ.get('TRACCAR_URL')

    if traccar_user and traccar_pass and traccar_url:
        auth = (traccar_user, traccar_pass)
        url_api = f"{traccar_url.rstrip('/')}/api/positions"
        try:
            response = requests.get(url_api, auth=auth, timeout=5)
            if response.status_code == 200:
                posicoes_traccar = response.json()
        except Exception as e:
            print(f"Erro ao conectar no Traccar: {e}")
    # --------------------------

    return render_template('mapa/index.html', acoes=acoes, positions=posicoes_traccar)