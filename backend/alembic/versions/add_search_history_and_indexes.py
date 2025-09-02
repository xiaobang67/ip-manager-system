"""Add search history table and performance indexes

Revision ID: search_history_001
Revises: 
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'search_history_001'
down_revision = None
depends_on = None


def upgrade():
    # Create search_history table
    op.create_table('search_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('search_name', sa.String(length=100), nullable=True),
        sa.Column('search_params', sa.JSON(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for search_history table
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('ix_search_history_is_favorite', 'search_history', ['is_favorite'])
    op.create_index('ix_search_history_updated_at', 'search_history', ['updated_at'])
    
    # Add performance indexes for IP addresses table
    op.create_index('ix_ip_addresses_subnet_status', 'ip_addresses', ['subnet_id', 'status'])
    op.create_index('ix_ip_addresses_status_allocated_at', 'ip_addresses', ['status', 'allocated_at'])
    op.create_index('ix_ip_addresses_device_type', 'ip_addresses', ['device_type'])
    op.create_index('ix_ip_addresses_location', 'ip_addresses', ['location'])
    op.create_index('ix_ip_addresses_assigned_to', 'ip_addresses', ['assigned_to'])
    
    # Add full-text search indexes (MySQL specific)
    op.execute("CREATE FULLTEXT INDEX ix_ip_addresses_fulltext ON ip_addresses(hostname, description)")
    op.execute("CREATE FULLTEXT INDEX ix_subnets_fulltext ON subnets(description)")
    
    # Add composite indexes for common query patterns
    op.create_index('ix_ip_addresses_subnet_ip', 'ip_addresses', ['subnet_id', 'ip_address'])
    op.create_index('ix_ip_addresses_allocated_by_at', 'ip_addresses', ['allocated_by', 'allocated_at'])
    
    # Add indexes for audit logs table for better search performance
    op.create_index('ix_audit_logs_entity_type_id', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_user_action_time', 'audit_logs', ['user_id', 'action', 'created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_audit_logs_user_action_time', 'audit_logs')
    op.drop_index('ix_audit_logs_entity_type_id', 'audit_logs')
    op.drop_index('ix_ip_addresses_allocated_by_at', 'ip_addresses')
    op.drop_index('ix_ip_addresses_subnet_ip', 'ip_addresses')
    
    # Drop full-text indexes
    op.execute("DROP INDEX ix_subnets_fulltext ON subnets")
    op.execute("DROP INDEX ix_ip_addresses_fulltext ON ip_addresses")
    
    # Drop performance indexes
    op.drop_index('ix_ip_addresses_assigned_to', 'ip_addresses')
    op.drop_index('ix_ip_addresses_location', 'ip_addresses')
    op.drop_index('ix_ip_addresses_device_type', 'ip_addresses')
    op.drop_index('ix_ip_addresses_status_allocated_at', 'ip_addresses')
    op.drop_index('ix_ip_addresses_subnet_status', 'ip_addresses')
    
    # Drop search_history indexes
    op.drop_index('ix_search_history_updated_at', 'search_history')
    op.drop_index('ix_search_history_is_favorite', 'search_history')
    op.drop_index('ix_search_history_user_id', 'search_history')
    
    # Drop search_history table
    op.drop_table('search_history')