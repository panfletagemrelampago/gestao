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

    # FILTRO DE AÇÕES
    if current_user.tipo_usuario == 'cliente':
        cliente = Cliente.query.filter_by(email=current_user.email).first()
        acoes = AcaoPromocional.query.filter_by(cliente_id=cliente.id).all() if cliente else []

    elif current_user.tipo_usuario == 'equipe':
        acoes = AcaoPromocional.query.filter_by(lider_equipe_id=current_user.id).all()

    else:
        acoes = AcaoPromocional.query.order_by(AcaoPromocional.data.desc()).all()


    return render_template(
        "mapa/index.html",
        acoes=acoes
    )