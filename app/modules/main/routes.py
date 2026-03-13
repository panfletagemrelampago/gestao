from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.equipe import Equipe
from app.models.veiculo import Veiculo
from app.models.auditoria import Auditoria
from app.models.material import Material
from app.models.vaga import Vaga
import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    hoje = datetime.date.today()
    
    # Dados globais para o dashboard
    acoes_dia = AcaoPromocional.query.all() # Simplificado para o MVP
    equipes_ativas = Equipe.query.filter_by(status=True).count()
    veiculos_em_campo = Veiculo.query.filter_by(status=False).count()
    ultimas_auditorias = Auditoria.query.order_by(Auditoria.data_hora.desc()).limit(5).all()
    
    # Novos contadores
    total_materiais = Material.query.count()
    total_vagas = Vaga.query.count()

    return render_template('main/dashboard.html', 
                           acoes_dia=acoes_dia, 
                           equipes_ativas=equipes_ativas,
                           veiculos_em_campo=veiculos_em_campo,
                           ultimas_auditorias=ultimas_auditorias,
                           total_materiais=total_materiais,
                           total_vagas=total_vagas,
                           date=datetime.date)
