import logging
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

def run_auto_migrations(app):
    """
    Executa migrações automáticas no startup da aplicação.
    Solução temporária para ambientes sem acesso a shell (ex: Render).
    """
    with app.app_context():
        try:
            # 1. Verificar se a coluna cliente_id existe na tabela users
            # Usamos uma query compatível com PostgreSQL e SQLite
            check_column_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='cliente_id';
            """)
            
            # Para SQLite (fallback caso não seja Postgres)
            check_sqlite_sql = text("PRAGMA table_info(users);")
            
            column_exists = False
            
            try:
                result = db.session.execute(check_column_sql).fetchone()
                if result:
                    column_exists = True
            except Exception:
                # Se falhar (provavelmente SQLite), tenta o método do SQLite
                result = db.session.execute(check_sqlite_sql).fetchall()
                for row in result:
                    if row[1] == 'cliente_id':
                        column_exists = True
                        break
            
            if not column_exists:
                logger.warning("Coluna 'cliente_id' não encontrada na tabela 'users'. Iniciando migração automática...")
                add_column_sql = text("ALTER TABLE users ADD COLUMN cliente_id INTEGER;")
                db.session.execute(add_column_sql)
                try:
                    add_fk_sql = text("""
                        ALTER TABLE users 
                        ADD CONSTRAINT fk_users_cliente_id 
                        FOREIGN KEY (cliente_id) 
                        REFERENCES clientes(id) 
                        ON DELETE SET NULL;
                    """)
                    db.session.execute(add_fk_sql)
                    logger.info("Constraint de Foreign Key 'fk_users_cliente_id' adicionada com sucesso.")
                except Exception as e:
                    logger.warning(f"Não foi possível adicionar a constraint de FK (pode ser SQLite): {str(e)}")
                db.session.commit()
                logger.warning("Migração automática concluída: Coluna 'cliente_id' adicionada à tabela 'users'.")
            else:
                logger.info("Verificação de schema: Coluna 'cliente_id' já existe na tabela 'users'.")

            # 4. Verificar se a coluna 'ativo' existe na tabela 'users'
            check_ativo_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='ativo';
            """)
            
            ativo_exists = False
            try:
                result = db.session.execute(check_ativo_sql).fetchone()
                if result:
                    ativo_exists = True
            except Exception:
                result = db.session.execute(check_sqlite_sql).fetchall()
                for row in result:
                    if row[1] == 'ativo':
                        ativo_exists = True
                        break
            
            if not ativo_exists:
                logger.warning("Coluna 'ativo' não encontrada na tabela 'users'. Iniciando migração automática...")
                add_ativo_sql = text("ALTER TABLE users ADD COLUMN ativo BOOLEAN DEFAULT TRUE;")
                db.session.execute(add_ativo_sql)
                db.session.commit()
                logger.warning("Migração automática concluída: Coluna 'ativo' adicionada à tabela 'users'.")
            else:
                logger.info("Verificação de schema: Coluna 'ativo' já existe na tabela 'users'.")
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro crítico durante a migração automática: {str(e)}")
            # Não interrompemos o startup do app, mas logamos o erro
