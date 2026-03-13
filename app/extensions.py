'''
Inicialização das extensões do Flask.

Este arquivo centraliza a criação das instâncias das extensões para evitar
importações circulares e organizar o projeto.
'''

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Instância do SQLAlchemy para interação com o banco de dados
db = SQLAlchemy()

# Instância do Flask-Migrate para gerenciamento de migrações do banco de dados
migrate = Migrate()

# Instância do Flask-Login para gerenciamento de autenticação de usuários
login_manager = LoginManager()
# Define a view de login para redirecionamento de usuários não autenticados
login_manager.login_view = 'auth.login'
# Mensagem a ser exibida para o usuário ao ser redirecionado para o login
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'
