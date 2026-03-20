import os
from app import create_app
from app.extensions import db
from sqlalchemy import text

def fix_database():
    app = create_app()
    with app.app_context():
        print("Iniciando correção do banco de dados...")
        try:
            # 1. Adicionar a coluna nome_campanha
            print("Tentando adicionar coluna 'nome_campanha' à tabela 'acoes_promocionais'...")
            db.session.execute(text("ALTER TABLE acoes_promocionais ADD COLUMN IF NOT EXISTS nome_campanha VARCHAR(255)"))
            db.session.commit()
            print("✅ Coluna 'nome_campanha' verificada/adicionada.")

            # 2. Atualizar a restrição de integridade para ON DELETE CASCADE
            # Primeiro, precisamos encontrar o nome da constraint da FK
            print("Ajustando restrição de integridade para ON DELETE CASCADE em 'fotos_auditoria'...")
            
            # SQL para PostgreSQL (Render usa Postgres)
            # Remove a constraint antiga e adiciona a nova com CASCADE
            sql_fix_fk = """
            DO $$ 
            BEGIN 
                -- Tenta remover a constraint se ela existir (nome padrão do SQLAlchemy costuma ser fotos_auditoria_turno_id_fkey)
                ALTER TABLE fotos_auditoria DROP CONSTRAINT IF EXISTS fotos_auditoria_turno_id_fkey;
                
                -- Adiciona a nova constraint com ON DELETE CASCADE
                ALTER TABLE fotos_auditoria 
                ADD CONSTRAINT fotos_auditoria_turno_id_fkey 
                FOREIGN KEY (turno_id) 
                REFERENCES turnos(id) 
                ON DELETE CASCADE;
            END $$;
            """
            db.session.execute(text(sql_fix_fk))
            db.session.commit()
            print("✅ Restrição ON DELETE CASCADE aplicada com sucesso.")
            
            print("\n🚀 Banco de dados sincronizado! O erro 500 deve desaparecer agora.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao atualizar banco de dados: {e}")
            print("\nSe o erro persistir, verifique se as credenciais do banco no Render estão corretas.")

if __name__ == "__main__":
    fix_database()
