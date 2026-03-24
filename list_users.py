from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print("--- LISTA DE UTILIZADORES ---")
    for u in users:
        print(f"Email: {u.email} | Tipo: {u.tipo_usuario} | Nome: {u.nome_exibicao}")
    print("-----------------------------")
