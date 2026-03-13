from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    nome_exibicao = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # HASH DA SENHA
    senha_hash = db.Column(db.Text, nullable=False)

    tipo_usuario = db.Column(
        db.Enum("admin", "equipe", "cliente", name="user_types"),
        nullable=False
    )

    device_id = db.Column(db.Integer, nullable=True)

    tema_preferido = db.Column(db.String(20), default="light")

    ativo = db.Column(db.Boolean, default=True)

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------
    # SENHA
    # -------------------------
    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)

    # -------------------------
    # REPRESENTAÇÃO
    # -------------------------
    def __repr__(self):
        return f"<User {self.email}>"