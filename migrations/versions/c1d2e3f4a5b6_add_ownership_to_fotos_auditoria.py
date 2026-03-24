"""add ownership fields to fotos_auditoria

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-03-23 00:00:00.000000

Objetivo:
- Adicionar usuario_id (FK para users.id) na tabela fotos_auditoria
- Adicionar cliente_id (FK para clientes.id) na tabela fotos_auditoria
- Preencher usuario_id retroativamente via join com Auditoria (quando possível)
- Preencher cliente_id retroativamente via join com Turno -> AcaoPromocional
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================
    # PASSO 1: Adicionar colunas de ownership (nullable)
    # =========================================================
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('usuario_id', sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('cliente_id', sa.Integer(), nullable=True)
        )

    # =========================================================
    # PASSO 2: Criar índices para performance
    # =========================================================
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.create_index('ix_fotos_auditoria_usuario_id', ['usuario_id'])
        batch_op.create_index('ix_fotos_auditoria_cliente_id', ['cliente_id'])

    # =========================================================
    # PASSO 3: Preencher usuario_id retroativamente via Auditoria
    # Fotos com auditoria_id podem herdar o user_id da auditoria
    # =========================================================
    op.execute("""
        UPDATE fotos_auditoria
        SET usuario_id = (
            SELECT a.user_id
            FROM auditorias a
            WHERE a.id = fotos_auditoria.auditoria_id
        )
        WHERE auditoria_id IS NOT NULL AND usuario_id IS NULL
    """)

    # =========================================================
    # PASSO 4: Preencher cliente_id retroativamente via Turno -> AcaoPromocional
    # =========================================================
    op.execute("""
        UPDATE fotos_auditoria
        SET cliente_id = (
            SELECT ap.cliente_id
            FROM turnos t
            JOIN acoes_promocionais ap ON ap.id = t.acao_id
            WHERE t.id = fotos_auditoria.turno_id
        )
        WHERE turno_id IS NOT NULL AND cliente_id IS NULL
    """)

    # =========================================================
    # PASSO 5: Adicionar FKs (opcionais, sem cascade para não quebrar dados legados)
    # =========================================================
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_fotos_auditoria_usuario_id',
            'users',
            ['usuario_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_fotos_auditoria_cliente_id',
            'clientes',
            ['cliente_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.drop_constraint('fk_fotos_auditoria_usuario_id', type_='foreignkey')
        batch_op.drop_constraint('fk_fotos_auditoria_cliente_id', type_='foreignkey')
        batch_op.drop_index('ix_fotos_auditoria_usuario_id')
        batch_op.drop_index('ix_fotos_auditoria_cliente_id')
        batch_op.drop_column('usuario_id')
        batch_op.drop_column('cliente_id')
