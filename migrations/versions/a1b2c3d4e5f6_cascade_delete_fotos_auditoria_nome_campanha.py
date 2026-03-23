"""cascade_delete_fotos_auditoria_nome_campanha

Revision ID: a1b2c3d4e5f6
Revises: f004268b695d
Create Date: 2026-03-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f004268b695d'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Adicionar coluna nome_campanha em acoes_promocionais
    # Reativado para consistência em futuras instalações do banco
    with op.batch_alter_table('acoes_promocionais', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('nome_campanha', sa.String(length=200), nullable=True)
        )

    # 2. Recriar FK turno_id em fotos_auditoria com ON DELETE CASCADE
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        # Nota: drop_constraint removido para evitar KeyError no SQLite
        batch_op.create_foreign_key(
            'fk_fotos_auditoria_turno_id',
            'turnos',
            ['turno_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade():
    # Reverter FK turno_id sem CASCADE
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fotos_auditoria_turno_id_fkey',
            'turnos',
            ['turno_id'],
            ['id']
        )

    # Remover coluna nome_campanha
    with op.batch_alter_table('acoes_promocionais', schema=None) as batch_op:
        batch_op.drop_column('nome_campanha')