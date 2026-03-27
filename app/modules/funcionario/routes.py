"""
Blueprint do módulo Funcionário.

Agrupa as rotas específicas para o perfil de funcionário (campo, registro de fotos,
materiais, etc.). Todas as rotas exigem o perfil 'funcionario' ou 'admin'.

URL prefix: /funcionario
"""
import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators.auth_decorators import perfil_required
from app.models.acao_promocional import AcaoPromocional
from app.models.auditoria import Auditoria
from app.models.material import Material
from app.models.turno import Turno
from app.extensions import db

funcionario_bp = Blueprint("funcionario", __name__, url_prefix="/funcionario")


@funcionario_bp.route("/")
@funcionario_bp.route("/dashboard")
@perfil_required("admin", "funcionario")
def dashboard():
    """
    Dashboard do funcionário: foco nas ações do dia e acesso rápido ao registro de fotos.
    """
    hoje = datetime.date.today()

    if current_user.tipo_usuario == "funcionario":
        # Funcionário vê apenas as ações em que é líder de equipe
        acoes_dia = AcaoPromocional.query.filter_by(
            lider_equipe_id=current_user.id
        ).filter(
            AcaoPromocional.status.in_(["Planejada", "Em Andamento"])
        ).order_by(AcaoPromocional.data.desc()).all()
        
        # Buscar turno ativo do funcionário (em qualquer ação)
        turno_ativo = Turno.query.filter(
            Turno.equipe_id == current_user.id,
            Turno.status.in_(['em andamento', 'pausado'])
        ).first()
    else:
        # Admin vê todas as ações ativas
        acoes_dia = AcaoPromocional.query.filter(
            AcaoPromocional.status.in_(["Planejada", "Em Andamento"])
        ).order_by(AcaoPromocional.data.desc()).all()
        turno_ativo = None

    return render_template(
        "funcionario/dashboard.html",
        acoes_dia=acoes_dia,
        turno_ativo=turno_ativo,
        hoje=hoje
    )


@funcionario_bp.route("/registrar-foto")
@perfil_required("admin", "funcionario")
def registrar_foto():
    """
    Redireciona para a rota de registro de foto do módulo de auditorias.
    Mantém compatibilidade com o blueprint existente.
    """
    return redirect(url_for("auditorias.registrar"))


@funcionario_bp.route("/materiais")
@perfil_required("admin", "funcionario")
def materiais():
    """
    Lista os materiais disponíveis para o funcionário.
    """
    materiais_lista = Material.query.order_by(Material.data_inicio.desc()).all()
    return render_template("funcionario/materiais.html", materiais=materiais_lista)


@funcionario_bp.route("/auditoria/<int:auditoria_id>")
@perfil_required("admin", "funcionario")
def detalhe_auditoria(auditoria_id):
    """
    Exibe o detalhe de uma auditoria registrada pelo próprio funcionário.
    Admin pode ver qualquer auditoria.
    """
    from app.utils.security_helpers import get_auditoria_segura
    auditoria = get_auditoria_segura(auditoria_id)
    return render_template("funcionario/detalhe_auditoria.html", auditoria=auditoria)
