from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.cliente import Cliente

app = create_app()
with app.app_context():
    # 1. Criar um Cliente de teste se não existir
    cliente = Cliente.query.filter_by(email="cliente_teste@empresa.com").first()
    if not cliente:
        cliente = Cliente(
            nome_empresa="Empresa de Teste",
            responsavel="João Cliente",
            telefone="11999999999",
            email="cliente_teste@empresa.com",
            cidade="São Paulo",
            estado="SP",
            status=True
        )
        db.session.add(cliente)
        db.session.commit()
        print(f"Cliente de teste criado: {cliente.nome_empresa}")
    else:
        print(f"Cliente de teste já existe: {cliente.nome_empresa}")

    # 2. Criar Usuário Cliente
    user_cliente = User.query.filter_by(email="cliente@teste.com").first()
    if not user_cliente:
        user_cliente = User(
            nome_exibicao="João Cliente",
            email="cliente@teste.com",
            tipo_usuario="cliente",
            cliente_id=cliente.id,
            ativo=True
        )
        user_cliente.set_password("cliente123")
        db.session.add(user_cliente)
        print("Usuário CLIENTE criado: cliente@teste.com / cliente123")
    else:
        print("Usuário CLIENTE já existe.")

    # 3. Criar Usuário Funcionário
    user_func = User.query.filter_by(email="func@teste.com").first()
    if not user_func:
        user_func = User(
            nome_exibicao="Maria Funcionária",
            email="func@teste.com",
            tipo_usuario="funcionario",
            ativo=True
        )
        user_func.set_password("func123")
        db.session.add(user_func)
        print("Usuário FUNCIONÁRIO criado: func@teste.com / func123")
    else:
        print("Usuário FUNCIONÁRIO já existe.")

    db.session.commit()
    print("Operação concluída com sucesso!")
