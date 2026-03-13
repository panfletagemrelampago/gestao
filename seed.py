from app import create_app, db
from app.models.user import User
import os

def seed_db():
    app = create_app()
    with app.app_context():
        # Cria o diretório instance se não existir
        instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print(f"Diretório {instance_path} criado.")

        # Cria todas as tabelas
        print("Criando tabelas no banco de dados...")
        db.create_all()
        
        # Verifica se o admin já existe
        admin_email = 'sac@relampagomt.com.br'
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            print(f"Criando usuário administrador: {admin_email}")
            admin = User(
                nome_exibicao='Administrador',
                email=admin_email,
                tipo_usuario='admin',
                ativo=True
            )
            admin.set_password('@Zadu020406#=')
            db.session.add(admin)
            db.session.commit()
            print("Usuário administrador criado com sucesso!")
        else:
            print("Usuário administrador já existe.")

if __name__ == '__main__':
    seed_db()
