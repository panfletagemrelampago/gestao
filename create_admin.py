from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():

    email = "sac@relampagomt.com.br"
    senha = "@Zadu020406#="

    user = User.query.filter_by(email=email).first()

    if user:
        user.set_password(senha)
        print("Senha do admin atualizada.")
    else:
        user = User(
            nome_exibicao="Administrador",
            email=email,
            tipo_usuario="admin",
            ativo=True
        )
        user.set_password(senha)
        db.session.add(user)
        print("Admin criado.")

    db.session.commit()

    print("Processo finalizado.")