"""add_auditoria_field_module

Revision ID: 0cc32966b7cc
Revises: 0bb21955a6bb
Create Date: 2026-03-13 12:00:00.000000

Adiciona as tabelas do módulo de auditoria de campo:
- turnos: controle de turnos de trabalho em campo
- areas_atuacao: polígonos GeoJSON das regiões de atuação
- fotos_auditoria: fotos geolocalizadas vinculadas a turnos
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cc32966b7cc'
down_revision = '0bb21955a6bb'
branch_labels = None
depends_on = None


def upgrade():
    # Verificar se as tabelas já existem (criadas via db.create_all)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'turnos' not in existing_tables:
        op.create_table(
            'turnos',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('acao_id', sa.Integer(), nullable=False),
            sa.Column('equipe_id', sa.Integer(), nullable=True),
            sa.Column('veiculo_id', sa.Integer(), nullable=True),
            sa.Column('inicio', sa.DateTime(), nullable=False),
            sa.Column('fim', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='ativo'),
            sa.Column('observacoes', sa.Text(), nullable=True),
            sa.Column('data_criacao', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['acao_id'], ['acoes_promocionais.id']),
            sa.ForeignKeyConstraint(['equipe_id'], ['equipes.id']),
            sa.ForeignKeyConstraint(['veiculo_id'], ['veiculos.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'areas_atuacao' not in existing_tables:
        op.create_table(
            'areas_atuacao',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('acao_id', sa.Integer(), nullable=False),
            sa.Column('nome', sa.String(150), nullable=False),
            sa.Column('descricao', sa.Text(), nullable=True),
            sa.Column('geojson', sa.Text(), nullable=True),
            sa.Column('cor', sa.String(20), nullable=True, server_default='#FF9E0C'),
            sa.Column('data_criacao', sa.DateTime(), nullable=True),
            sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['acao_id'], ['acoes_promocionais.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'fotos_auditoria' not in existing_tables:
        op.create_table(
            'fotos_auditoria',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('turno_id', sa.Integer(), nullable=True),
            sa.Column('auditoria_id', sa.Integer(), nullable=True),
            sa.Column('url', sa.String(500), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('descricao', sa.Text(), nullable=True),
            sa.Column('dentro_da_area', sa.Boolean(), nullable=True),
            sa.Column('data_hora', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['turno_id'], ['turnos.id']),
            sa.ForeignKeyConstraint(['auditoria_id'], ['auditorias.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'fotos_auditoria' in existing_tables:
        op.drop_table('fotos_auditoria')
    if 'areas_atuacao' in existing_tables:
        op.drop_table('areas_atuacao')
    if 'turnos' in existing_tables:
        op.drop_table('turnos')
