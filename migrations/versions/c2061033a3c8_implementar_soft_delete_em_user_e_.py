from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'c2061033a3c8'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def column_exists(inspector, table_name, column_name):
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def fk_exists(inspector, table_name, fk_name):
    fks = inspector.get_foreign_keys(table_name)
    return any(fk['name'] == fk_name for fk in fks)


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # --- Alterações na tabela 'users' ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        if not column_exists(inspector, 'users', 'ativo'):
            batch_op.add_column(
                sa.Column(
                    'ativo',
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text('true')
                )
            )

        batch_op.alter_column(
            'ativo',
            existing_type=sa.Boolean(),
            nullable=False,
            existing_server_default=sa.text('true')
        )

    # --- Alterações na tabela 'auditorias' ---
    with op.batch_alter_table('auditorias', schema=None) as batch_op:
        batch_op.alter_column(
            'user_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )

        existing_fks = inspector.get_foreign_keys('auditorias')
        fk_name_to_drop = None

        for fk in existing_fks:
            if 'user_id' in fk['constrained_columns'] and fk['referred_table'] == 'users':
                fk_name_to_drop = fk['name']
                break

        if fk_name_to_drop:
            batch_op.drop_constraint(fk_name_to_drop, type_='foreignkey')

        new_fk_name = 'fk_auditorias_user_id_ondelete_set_null'

        if not fk_exists(inspector, 'auditorias', new_fk_name):
            batch_op.create_foreign_key(
                new_fk_name,
                'users',
                ['user_id'],
                ['id'],
                ondelete='SET NULL'
            )


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # --- Reverter alterações na tabela 'auditorias' ---
    with op.batch_alter_table('auditorias', schema=None) as batch_op:
        batch_op.alter_column(
            'user_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )

        existing_fks = inspector.get_foreign_keys('auditorias')
        fk_name_to_drop = None

        for fk in existing_fks:
            if 'user_id' in fk['constrained_columns'] and fk['referred_table'] == 'users':
                fk_name_to_drop = fk['name']
                break

        if fk_name_to_drop:
            batch_op.drop_constraint(fk_name_to_drop, type_='foreignkey')

        original_fk_name = 'fk_auditorias_user_id'

        if not fk_exists(inspector, 'auditorias', original_fk_name):
            batch_op.create_foreign_key(
                original_fk_name,
                'users',
                ['user_id'],
                ['id']
            )

    # --- Reverter alterações na tabela 'users' ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        if column_exists(inspector, 'users', 'ativo'):
            batch_op.drop_column('ativo')