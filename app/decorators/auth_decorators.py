"""
Decoradores de autorização para controle de acesso por perfil de usuário.

Uso:
    @perfil_required("admin")
    @perfil_required("admin", "funcionario")
    @perfil_required("admin", "funcionario", "cliente")
"""
import logging
from functools import wraps
from flask import abort, request
from flask_login import current_user

logger = logging.getLogger(__name__)


def perfil_required(*tipos_permitidos):
    """
    Decorator para restringir o acesso a rotas com base no tipo de usuário.

    Distingue claramente entre:
    - 401 Unauthorized: usuário não autenticado
    - 403 Forbidden: usuário autenticado, mas sem permissão

    Args:
        *tipos_permitidos: tipos de usuário permitidos (ex: "admin", "funcionario", "cliente")
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                logger.warning(
                    f"Acesso não autenticado tentado em {request.path}"
                )
                abort(401, description="Você precisa estar logado para acessar esta página.")

            if current_user.tipo_usuario not in tipos_permitidos:
                logger.warning(
                    f"Acesso negado: user={current_user.id} "
                    f"({current_user.tipo_usuario}), rota={request.path}, "
                    f"perfis_permitidos={tipos_permitidos}"
                )
                abort(403, description="Acesso negado. Você não tem permissão para acessar esta página.")

            return f(*args, **kwargs)
        return wrapper
    return decorator
