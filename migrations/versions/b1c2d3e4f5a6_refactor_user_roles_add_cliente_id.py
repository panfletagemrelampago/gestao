"""refactor user roles and add cliente_id

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-23 00:00:00.000000

Objetivo:
- Substituir os tipos 'diretoria' e 'motorista' pelo tipo unificado 'funcionario'
- Adicionar o campo cliente_id (FK para clientes.id) na tabela users
- Garantir que usuários existentes com 'diretoria' ou 'motorista' sejam migrados para 'funcionario'
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================
    # PASSO 1: Adicionar coluna cliente_id (nullable)
    # =========================================================
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('cliente_id', sa.Integer(), nullable=True)
        )

    # =========================================================
    # PASSO 2: Migrar dados — converter 'diretoria' e 'motorista'
    # para 'funcionario' antes de alterar o Enum
    # =========================================================
    op.execute(
        "UPDATE users SET tipo_usuario = 'funcionario' "
        "WHERE tipo_usuario IN ('diretoria', 'motorista', 'equipe')"
    )

    # =========================================================
    # PASSO 3: Alterar o tipo Enum para os novos valores
    # Nota: SQLite não suporta ALTER COLUMN nativo, mas o
    # batch_alter_table do Alembic lida com isso via recreate.
    # =========================================================
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'tipo_usuario',
            existing_type=sa.Enum(
                'admin', 'diretoria', 'cliente', 'motorista',
                name='user_types'
            ),
            type_=sa.Enum(
                'admin', 'funcionario', 'cliente',
                name='user_types'
            ),
            existing_nullable=False
        )

    # =========================================================
    # PASSO 4: Adicionar FK para clientes.id
    # =========================================================
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_users_cliente_id',
            'clientes',
            ['cliente_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade():
    # =========================================================
    # REVERTER: Remover FK e coluna cliente_id, restaurar Enum antigo
    # =========================================================
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_cliente_id', type_='foreignkey')
        batch_op.drop_column('cliente_id')
        batch_op.alter_column(
            'tipo_usuario',
            existing_type=sa.Enum(
                'admin', 'funcionario', 'cliente',
                name='user_types'
            ),
            type_=sa.Enum(
                'admin', 'diretoria', 'cliente', 'motorista',
                name='user_types'
            ),
            existing_nullable=False
        )
