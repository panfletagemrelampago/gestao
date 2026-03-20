"""
Arquivo de configuração da aplicação Flask.

Carrega variáveis de ambiente a partir de um arquivo .env e define as configurações
para a aplicação, banco de dados e serviços externos.
"""

import os
from dotenv import load_dotenv

# Diretório raiz do projeto
basedir = os.path.abspath(os.path.dirname(__file__))

# Carregar variáveis do .env
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Classe de configuração principal da aplicação."""

    # Segurança
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "uma-chave-secreta-bem-dificil-de-adivinhar"
    )

    # Configuração do banco
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # Corrigir prefixo do Render (postgres -> postgresql)
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "instance", "app.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False



    # Configuração da API do Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")

    # Timezone (Horário de Cuiabá - UTC-4)
    TIMEZONE = 'America/Cuiaba'

    # Outras configurações
    ITEMS_PER_PAGE = 10
