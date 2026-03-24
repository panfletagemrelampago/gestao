import logging
from flask_migrate import upgrade

logger = logging.getLogger(__name__)

def run_migrations(app):
    with app.app_context():
        try:
            upgrade()
            logger.info("Alembic migrations executadas com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao executar Alembic migrations: {str(e)}")
