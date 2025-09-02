"""Add custom fields and tags tables

Revision ID: 002_add_custom_fields_and_tags
Revises: add_search_history_and_indexes
Create Date: 2025-01-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002_add_custom_fields_and_tags'
down_revision = 'add_search_history_and_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Create custom_fields table
    op.create_table('custom_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.Enum('ip', 'subnet', name='entitytype'), nullable=False),
        sa.Column('field_name', sa.String(length=50), nullable=False),
        sa.Column('field_type', sa.Enum('text', 'number', 'date', 'select', name='fieldtype'), nullable=False),
        sa.Column('field_options', sa.JSON(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_fields_id'), 'custom_fields', ['id'], unique=False)
    op.create_index(op.f('ix_custom_fields_entity_type'), 'custom_fields', ['entity_type'], unique=False)
    op.create_index(op.f('ix_custom_fields_field_name'), 'custom_fields', ['field_name'], unique=False)

    # Create custom_field_values table
    op.create_table('custom_field_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.Enum('ip', 'subnet', name='entitytype'), nullable=False),
        sa.Column('field_value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['field_id'], ['custom_fields.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('field_id', 'entity_id', 'entity_type', name='unique_field_entity')
    )
    op.create_index(op.f('ix_custom_field_values_id'), 'custom_field_values', ['id'], unique=False)
    op.create_index(op.f('ix_custom_field_values_entity_id'), 'custom_field_values', ['entity_id'], unique=False)
    op.create_index(op.f('ix_custom_field_values_entity_type'), 'custom_field_values', ['entity_type'], unique=False)

    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=False)

    # Create ip_tags association table
    op.create_table('ip_tags',
        sa.Column('ip_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['ip_id'], ['ip_addresses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('ip_id', 'tag_id')
    )

    # Create subnet_tags association table
    op.create_table('subnet_tags',
        sa.Column('subnet_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['subnet_id'], ['subnets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('subnet_id', 'tag_id')
    )


def downgrade():
    # Drop association tables first
    op.drop_table('subnet_tags')
    op.drop_table('ip_tags')
    
    # Drop tags table
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
    
    # Drop custom field values table
    op.drop_index(op.f('ix_custom_field_values_entity_type'), table_name='custom_field_values')
    op.drop_index(op.f('ix_custom_field_values_entity_id'), table_name='custom_field_values')
    op.drop_index(op.f('ix_custom_field_values_id'), table_name='custom_field_values')
    op.drop_table('custom_field_values')
    
    # Drop custom fields table
    op.drop_index(op.f('ix_custom_fields_field_name'), table_name='custom_fields')
    op.drop_index(op.f('ix_custom_fields_entity_type'), table_name='custom_fields')
    op.drop_index(op.f('ix_custom_fields_id'), table_name='custom_fields')
    op.drop_table('custom_fields')