"""
Utilitários de controle de acesso e bootstrap do sistema.

REFATORAÇÃO (Passo 1):
- get_auditoria_segura() migrada para operar sobre FotoAuditoria
  (campo usuario_id no lugar de user_id).
- Importação de Auditoria removida.
"""
import logging
import os
from flask import abort
from flask_login import current_user
from app.extensions import db
from app.models.acao_promocional import AcaoPromocional
from app.models.foto_auditoria import FotoAuditoria
from app.models.user import User
from sqlalchemy import inspect

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
        query = query.filter_by(lider_equipe_id=current_user.id)
    return query.first_or_404(description="Ação não encontrada ou acesso negado.")


def get_auditoria_segura(foto_id):
    """
    Retorna uma FotoAuditoria com base no ID, aplicando filtros de ownership.
    - Admin: vê qualquer foto.
    - Funcionario: vê apenas fotos que ele próprio registrou (usuario_id).
    - Cliente: não tem acesso direto (acessa via ações).
    Retorna 404 se não encontrada, 403 se acesso negado.

    REFATORAÇÃO: operava sobre Auditoria; agora opera sobre FotoAuditoria.
    """
    if current_user.tipo_usuario == "cliente":
        logger.warning(
            f"Cliente tentou acessar foto {foto_id} diretamente: "
            f"user={current_user.id}"
        )
        abort(403, description="Clientes não têm acesso direto a registros de campo.")
    query = FotoAuditoria.query.filter_by(id=foto_id)
    if current_user.tipo_usuario == "funcionario":
        query = query.filter_by(usuario_id=current_user.id)
    return query.first_or_404(description="Registro não encontrado ou acesso negado.")


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
    """
    if user.tipo_usuario == "cliente":
        return user.cliente_id
    return None


def setup_admin(app):
    """
    Garante a existência de um usuário administrador inicial.
    Não sobrescreve nome ou senha se o usuário já existir.
    """
    with app.app_context():
        admin_email = "sac@relampagomt.com.br"
        admin_password = os.environ.get("ADMIN_PASSWORD", "@Zadu0204")
        admin_name = os.environ.get("ADMIN_USERNAME", "Relam")

        inspector = inspect(db.engine)
        if not inspector.has_table("users"):
            logger.info("Tabela 'users' não encontrada. Pulando setup_admin.")
            return

        user = User.query.filter_by(email=admin_email).first()

        if not user:
            new_admin = User(
                nome_exibicao=admin_name,
                email=admin_email,
                tipo_usuario="admin",
                ativo=True
            )
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            db.session.commit()
            print(f"ADMIN INICIAL CRIADO: {admin_email}")
        else:
            logger.info(f"Admin {admin_email} já existe. Nenhuma alteração aplicada.")
