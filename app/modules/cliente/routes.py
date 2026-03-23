"""
Blueprint do módulo Cliente.

Agrupa as rotas específicas para o perfil de cliente (visualização de ações,
mapa em tempo real, relatórios). Todas as rotas são somente leitura.

URL prefix: /cliente
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.decorators.auth_decorators import perfil_required
from app.utils.security_helpers import get_acao_segura, get_acoes_por_perfil
from app.models.acao_promocional import AcaoPromocional

cliente_bp = Blueprint("cliente", __name__, url_prefix="/cliente")


@cliente_bp.route("/")
@cliente_bp.route("/dashboard")
@perfil_required("admin", "cliente")
def dashboard():
    """
    Dashboard do cliente: foco no mapa em tempo real e visualização das suas ações.
    Filtra as ações pelo cliente_id do usuário autenticado.
    """
    acoes = get_acoes_por_perfil()
    return render_template("cliente/dashboard.html", acoes=acoes)


@cliente_bp.route("/mapa")
@perfil_required("admin", "cliente")
def mapa():
    """
    Redireciona para o mapa existente, que já possui filtros por cliente.
    """
    return redirect(url_for("mapa.index"))


@cliente_bp.route("/acao/<int:acao_id>")
@perfil_required("admin", "cliente")
def ver_acao(acao_id):
    """
    Exibe o detalhe de uma ação promocional com proteção de ownership.
    O cliente só pode ver ações vinculadas ao seu cliente_id.
    """
    acao = get_acao_segura(acao_id)
    return render_template("cliente/detalhe_acao.html", acao=acao)


@cliente_bp.route("/relatorio/<int:acao_id>")
@perfil_required("admin", "cliente")
def relatorio(acao_id):
    """
    Redireciona para o relatório detalhado da ação no módulo de auditorias.
    Aplica verificação de ownership antes do redirecionamento.
    """
    # Verifica ownership antes de redirecionar
    acao = get_acao_segura(acao_id)
    return redirect(url_for("auditorias.relatorio", acao_id=acao_id))
