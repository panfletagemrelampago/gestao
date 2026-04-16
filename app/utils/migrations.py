import logging
# from flask_migrate import upgrade  # DESATIVADO TEMPORARIAMENTE
from sqlalchemy import inspect, text
from app.extensions import db

logger = logging.getLogger(__name__)


def run_migrations(app):
    with app.app_context():
        # 1. Migrações do Alembic (DESATIVADAS)
        try:
            # upgrade()  # ← DESATIVADO para evitar DuplicateTable
            logger.info("Migrações automáticas desativadas (banco já estruturado).")
        except Exception as e:
            logger.error(f"Erro ao executar Alembic migrations: {str(e)}")

        # 2. Verificação manual de colunas críticas (fallback)
        try:
            inspector = inspect(db.engine)

            # Verificar tabela 'turnos'
            if 'turnos' in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns('turnos')]
                if 'pausas_json' not in columns:
                    logger.warning("Coluna 'pausas_json' ausente na tabela 'turnos'. Tentando adicionar manualmente...")
                    db.session.execute(text("ALTER TABLE turnos ADD COLUMN pausas_json TEXT DEFAULT '[]'"))
                    db.session.commit()
                    logger.info("Coluna 'pausas_json' adicionada com sucesso.")

            # Verificar tabela 'mapa_areas'
            if 'mapa_areas' in inspector.get_table_names():
                columns = [c['name'] for c in inspector.get_columns('mapa_areas')]
                if 'descricao' not in columns:
                    logger.warning(
                        "Coluna 'descricao' ausente na tabela 'mapa_areas'. Tentando adicionar manualmente...")
                    db.session.execute(text("ALTER TABLE mapa_areas ADD COLUMN descricao TEXT"))
                    db.session.commit()
                    logger.info("Coluna 'descricao' adicionada com sucesso.")

        except Exception as e:
            logger.error(f"Erro na verificação manual de colunas: {str(e)}")
            db.session.rollback()