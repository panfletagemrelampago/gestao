import os
from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # =============================
    # EXTENSIONS
    # =============================
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # =============================
    # MODELS
    # =============================
    from app.models.user import User

    # =============================
    # BLUEPRINTS
    # =============================

    # AUTH
    from app.modules.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # MAIN
    from app.modules.main.routes import main_bp
    app.register_blueprint(main_bp)

    # CLIENTES
    from app.modules.clientes.routes import clientes_bp
    app.register_blueprint(clientes_bp, url_prefix="/clientes")

    # EQUIPE
    from app.modules.equipe.routes import equipe_bp
    app.register_blueprint(equipe_bp, url_prefix="/equipe")

    # VEICULOS
    from app.modules.veiculos.routes import veiculos_bp
    app.register_blueprint(veiculos_bp, url_prefix="/veiculos")

    # ACOES
    from app.modules.acoes.routes import acoes_bp
    app.register_blueprint(acoes_bp, url_prefix="/acoes")

    # AUDITORIAS
    from app.modules.auditorias.routes import auditorias_bp
    app.register_blueprint(auditorias_bp, url_prefix="/auditorias")

    # MAPA (TELA)
    from app.modules.mapa.routes import mapa_bp
    app.register_blueprint(mapa_bp, url_prefix="/mapa")

    # API GERAL
    from app.modules.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # 🔥 NOVO — API DO MAPA
    from app.modules.api.mapa import bp as mapa_api_bp
    app.register_blueprint(mapa_api_bp, url_prefix="/api")

    # MATERIAIS
    from app.modules.materiais.routes import materiais_bp
    app.register_blueprint(materiais_bp, url_prefix="/materiais")

    # VAGAS
    from app.modules.vagas.routes import vagas_bp
    app.register_blueprint(vagas_bp, url_prefix="/vagas")

    # =============================
    # LOGIN MANAGER
    # =============================
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # =============================
    # INIT DB + ADMIN
    # =============================
    with app.app_context():
        db.create_all()

        admin_email = "sac@relampagomt.com.br"
        admin_password = os.environ.get("ADMIN_PASSWORD", "@Zadu0204")
        admin_name = os.environ.get("ADMIN_USERNAME", "Relam")

        # remove admin antigo
        user_antigo = User.query.filter_by(email="admin@agencia.com").first()
        if user_antigo:
            db.session.delete(user_antigo)
            db.session.commit()

        # cria ou atualiza admin
        user = User.query.filter_by(email=admin_email).first()

        if not user:
            new_admin = User(
                nome_exibicao=admin_name,
                email=admin_email,
                tipo_usuario="admin",
                ativo=True
            )
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            db.session.commit()
            print(f"ADMIN REAL CRIADO: {admin_email}")
        else:
            user.nome_exibicao = admin_name
            user.set_password(admin_password)
            db.session.commit()
            print(f"ADMIN SINCRONIZADO: {admin_email}")

    return app