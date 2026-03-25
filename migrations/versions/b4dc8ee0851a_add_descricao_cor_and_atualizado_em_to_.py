"""Add descricao, cor and atualizado_em to MapaArea

Revision ID: b4dc8ee0851a
Revises: c2061033a3c8
Create Date: 2026-03-24 22:46:03.008274
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4dc8ee0851a'
down_revision = 'c2061033a3c8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mapa_areas', sa.Column('descricao', sa.Text(), nullable=True))
    op.add_column('mapa_areas', sa.Column('cor', sa.String(length=7), nullable=True))
    op.add_column('mapa_areas', sa.Column('atualizado_em', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('mapa_areas', 'atualizado_em')
    op.drop_column('mapa_areas', 'cor')
    op.drop_column('mapa_areas', 'descricao')