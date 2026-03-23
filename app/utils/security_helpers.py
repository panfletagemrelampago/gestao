"""
Helpers de segurança para controle de acesso por ownership (posse de dados).

Garante que cada perfil de usuário acesse apenas os dados aos quais tem direito:
- admin: acesso a todos os dados
- funcionario: acesso às ações em que é líder e às auditorias que registrou
- cliente: acesso apenas às ações/auditorias vinculadas ao seu cliente_id
"""
import logging
from flask import abort
from flask_login import current_user
from app.models.acao_promocional import AcaoPromocional
from app.models.auditoria import Auditoria

logger = logging.getLogger(__name__)


def get_acao_segura(acao_id):
    """
    Retorna uma AcaoPromocional com base no ID, aplicando filtros de ownership.

    - Admin: vê qualquer ação.
    - Funcionario: vê apenas ações em que é líder de equipe.
    - Cliente: vê apenas ações vinculadas ao seu cliente_id.

    Retorna 404 se não encontrada ou 403 se acesso negado.
    """
    query = AcaoPromocional.query.filter_by(id=acao_id)

    if current_user.tipo_usuario == "cliente":
        if not current_user.cliente_id:
            logger.warning(
                f"Cliente sem vínculo tentou acessar ação {acao_id}: "
                f"user={current_user.id}"
            )
            abort(403, description="Usuário cliente sem vínculo de cliente associado.")
        query = query.filter_by(cliente_id=current_user.cliente_id)

    elif current_user.tipo_usuario == "funcionario":
        # Funcionário só vê ações em que é líder de equipe
        query = query.filter_by(lider_equipe_id=current_user.id)

    # Admin não tem filtro adicional

    return query.first_or_404(description="Ação não encontrada ou acesso negado.")


def get_auditoria_segura(auditoria_id):
    """
    Retorna uma Auditoria com base no ID, aplicando filtros de ownership.

    - Admin: vê qualquer auditoria.
    - Funcionario: vê apenas auditorias que ele próprio registrou.
    - Cliente: não tem acesso direto a auditorias (acessa via ações).

    Retorna 404 se não encontrada, 403 se acesso negado.
    """
    if current_user.tipo_usuario == "cliente":
        logger.warning(
            f"Cliente tentou acessar auditoria {auditoria_id} diretamente: "
            f"user={current_user.id}"
        )
        abort(403, description="Clientes não têm acesso direto a auditorias.")

    query = Auditoria.query.filter_by(id=auditoria_id)

    if current_user.tipo_usuario == "funcionario":
        # Funcionário só vê auditorias que ele próprio registrou
        query = query.filter_by(user_id=current_user.id)

    # Admin não tem filtro adicional

    return query.first_or_404(description="Auditoria não encontrada ou acesso negado.")


def get_acoes_por_perfil():
    """
    Retorna a lista de ações filtrada conforme o perfil do usuário atual.

    - Admin: todas as ações.
    - Funcionario: ações em que é líder de equipe.
    - Cliente: ações vinculadas ao seu cliente_id.
    """
    if current_user.tipo_usuario == "admin":
        return AcaoPromocional.query.all()

    elif current_user.tipo_usuario == "funcionario":
        return AcaoPromocional.query.filter_by(
            lider_equipe_id=current_user.id
        ).all()

    elif current_user.tipo_usuario == "cliente":
        if not current_user.cliente_id:
            logger.warning(
                f"Cliente sem vínculo tentou listar ações: user={current_user.id}"
            )
            return []
        return AcaoPromocional.query.filter_by(
            cliente_id=current_user.cliente_id
        ).all()

    return []


def get_cliente_id_do_usuario(user):
    """
    Retorna o cliente_id vinculado ao usuário.

    Para clientes, usa diretamente o campo cliente_id do modelo User.
    Para admin/funcionario, retorna None (sem restrição de cliente).

    Substitui o padrão antigo de busca por email na tabela Cliente.
    """
    if user.tipo_usuario == "cliente":
        return user.cliente_id
    return None
