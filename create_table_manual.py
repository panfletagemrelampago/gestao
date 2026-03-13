import os
import sys
from datetime import datetime

# Adiciona o diretório 'gestao' ao path para que o Python encontre o pacote 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'gestao')))

try:
    from app import create_app
    from app.extensions import db
    # Importa o model para garantir que o SQLAlchemy o conheça
    from app.models.mapa_area import MapaArea

    print("Iniciando criação da tabela 'mapa_areas'...")

    app = create_app()
    with app.app_context():
        # O comando create_all() cria apenas as tabelas que ainda não existem
        db.create_all()
        print("--------------------------------------------------")
        print("SUCESSO! A tabela 'mapa_areas' foi criada com sucesso.")
        print("Agora você já pode desenhar áreas e elas serão salvas.")
        print("--------------------------------------------------")

except Exception as e:
    print("--------------------------------------------------")
    print(f"ERRO AO CRIAR TABELA: {e}")
    print("Verifique se as variáveis de ambiente (DATABASE_URL) estão corretas.")
    print("--------------------------------------------------")
