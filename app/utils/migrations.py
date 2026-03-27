import logging
from flask_migrate import upgrade
from sqlalchemy import inspect, text
from app.extensions import db

logger = logging.getLogger(__name__)

def run_migrations(app):
    with app.app_context():
        # 1. Tentar executar as migrações normais do Alembic
        try:
            upgrade()
            logger.info("Alembic migrations executadas com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao executar Alembic migrations: {str(e)}")
            # Se falhar, continuamos para a verificação manual de colunas críticas

        # 2. Verificação manual de colunas críticas (Fallback para ambientes onde o Alembic falha)
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
                    logger.warning("Coluna 'descricao' ausente na tabela 'mapa_areas'. Tentando adicionar manualmente...")
                    db.session.execute(text("ALTER TABLE mapa_areas ADD COLUMN descricao TEXT"))
                    db.session.commit()
                    logger.info("Coluna 'descricao' adicionada com sucesso.")
                    
        except Exception as e:
            logger.error(f"Erro na verificação manual de colunas: {str(e)}")
            db.session.rollback()
