"""Refactor Passo1+Passo2: adiciona acao_id em fotos_auditoria, remove auditoria_id,
cria índices compostos em posicoes_gps e fotos_auditoria.

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-03-28

Descrição das mudanças:
1. Adiciona coluna acao_id (FK → acoes_promocionais) em fotos_auditoria.
2. Backfill de acao_id a partir de turnos.acao_id via turno_id existente.
3. Remove coluna auditoria_id (ponte legada para tabela auditorias).
4. Cria índice composto (device_id, data_hora DESC) em posicoes_gps.
5. Cria índice composto (acao_id, data_hora DESC) em fotos_auditoria.
6. Cria índice composto (turno_id, data_hora DESC) em fotos_auditoria.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Adicionar coluna acao_id em fotos_auditoria ────────────────────────
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('acao_id', sa.Integer(), nullable=True)
        )

    # ── 2. Backfill: preencher acao_id a partir de turnos.acao_id ─────────────
    op.execute("""
        UPDATE fotos_auditoria fa
        SET acao_id = t.acao_id
        FROM turnos t
        WHERE fa.turno_id = t.id
          AND fa.acao_id IS NULL
    """)

    # ── 3. Criar FK para acoes_promocionais ───────────────────────────────────
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_fotos_auditoria_acao_id',
            'acoes_promocionais',
            ['acao_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # ── 4. Remover coluna auditoria_id (ponte legada) ─────────────────────────
    # Primeiro remover FK e índice existentes, depois a coluna
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        # Tentar remover FK (nome pode variar conforme ambiente)
        try:
            batch_op.drop_constraint('fotos_auditoria_auditoria_id_fkey', type_='foreignkey')
        except Exception:
            pass
        try:
            batch_op.drop_index('ix_fotos_auditoria_auditoria_id')
        except Exception:
            pass
        batch_op.drop_column('auditoria_id')

    # ── 5. Índice composto em posicoes_gps (device_id, data_hora DESC) ────────
    op.create_index(
        'ix_posicoes_gps_device_data',
        'posicoes_gps',
        ['device_id', sa.text('data_hora DESC')],
        unique=False
    )

    # ── 6. Índice composto em fotos_auditoria (acao_id, data_hora DESC) ───────
    op.create_index(
        'ix_fotos_auditoria_acao_data',
        'fotos_auditoria',
        ['acao_id', sa.text('data_hora DESC')],
        unique=False
    )

    # ── 7. Índice composto em fotos_auditoria (turno_id, data_hora DESC) ──────
    op.create_index(
        'ix_fotos_auditoria_turno_data',
        'fotos_auditoria',
        ['turno_id', sa.text('data_hora DESC')],
        unique=False
    )


def downgrade():
    # Remover índices compostos
    op.drop_index('ix_fotos_auditoria_turno_data', table_name='fotos_auditoria')
    op.drop_index('ix_fotos_auditoria_acao_data', table_name='fotos_auditoria')
    op.drop_index('ix_posicoes_gps_device_data', table_name='posicoes_gps')

    # Restaurar coluna auditoria_id
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('auditoria_id', sa.Integer(), nullable=True)
        )
        batch_op.create_index('ix_fotos_auditoria_auditoria_id', ['auditoria_id'])
        batch_op.create_foreign_key(
            'fotos_auditoria_auditoria_id_fkey',
            'auditorias',
            ['auditoria_id'],
            ['id']
        )

    # Remover FK e coluna acao_id
    with op.batch_alter_table('fotos_auditoria', schema=None) as batch_op:
        batch_op.drop_constraint('fk_fotos_auditoria_acao_id', type_='foreignkey')
        batch_op.drop_column('acao_id')
