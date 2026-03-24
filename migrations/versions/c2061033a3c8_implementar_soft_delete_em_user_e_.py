from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'c2061033a3c8'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # --- Alterações na tabela 'users' ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Adicionar coluna 'ativo' se não existir
        if not inspector.has_column('users', 'ativo'):
            batch_op.add_column(sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')))
        # Garantir que a coluna 'ativo' não seja nullable e tenha default
        batch_op.alter_column('ativo',
               existing_type=sa.Boolean(),
               nullable=False,
               existing_server_default=sa.text('true'))

    # --- Alterações na tabela 'auditorias' ---
    with op.batch_alter_table('auditorias', schema=None) as batch_op:
        # Tornar 'user_id' nullable
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

        # Remover a FK existente e criar uma nova com ON DELETE SET NULL
        # É necessário verificar se a FK existe antes de tentar removê-la
        # e se a nova FK ainda não existe antes de criá-la.
        # Alembic não autogera nomes de FKs, então precisamos inspecionar.
        existing_fks = inspector.get_foreign_keys('auditorias')
        fk_name_to_drop = None
        for fk in existing_fks:
            if 'user_id' in fk['constrained_columns'] and fk['referred_table'] == 'users':
                fk_name_to_drop = fk['name']
                break

        if fk_name_to_drop:
            batch_op.drop_constraint(fk_name_to_drop, type_='foreignkey')

        # Criar a nova FK com ON DELETE SET NULL
        # Verificar se a FK já existe para evitar erro em re-execução
        # Alembic não autogera nomes de FKs, então vamos usar um nome explícito
        # para facilitar a idempotência e o downgrade.
        new_fk_name = 'fk_auditorias_user_id_ondelete_set_null'
        if not any(fk['name'] == new_fk_name for fk in inspector.get_foreign_keys('auditorias')):
            batch_op.create_foreign_key(new_fk_name, 'users', ['user_id'], ['id'], ondelete='SET NULL')

def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # --- Reverter alterações na tabela 'auditorias' ---
    with op.batch_alter_table('auditorias', schema=None) as batch_op:
        # Reverter 'user_id' para non-nullable
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)

        # Remover a FK com ON DELETE SET NULL e recriar a original (sem ON DELETE)
        existing_fks = inspector.get_foreign_keys('auditorias')
        fk_name_to_drop = None
        for fk in existing_fks:
            if 'user_id' in fk['constrained_columns'] and fk['referred_table'] == 'users':
                fk_name_to_drop = fk['name']
                break

        if fk_name_to_drop:
            batch_op.drop_constraint(fk_name_to_drop, type_='foreignkey')

        # Recriar a FK original (sem ON DELETE SET NULL)
        original_fk_name = 'fk_auditorias_user_id'
        if not any(fk['name'] == original_fk_name for fk in inspector.get_foreign_keys('auditorias')):
            batch_op.create_foreign_key(original_fk_name, 'users', ['user_id'], ['id'])

    # --- Reverter alterações na tabela 'users' ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Remover a coluna 'ativo' se existir
        if inspector.has_column('users', 'ativo'):
            batch_op.drop_column('ativo')
