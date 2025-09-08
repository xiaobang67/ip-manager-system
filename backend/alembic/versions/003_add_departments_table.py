"""Add departments table

Revision ID: 003_add_departments_table
Revises: 002_add_custom_fields_and_tags
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('manager', sa.String(length=100), nullable=True),
        sa.Column('contact_email', sa.String(length=100), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)
    op.create_index(op.f('ix_departments_name'), 'departments', ['name'], unique=True)
    op.create_index(op.f('ix_departments_code'), 'departments', ['code'], unique=True)
    op.create_index(op.f('ix_departments_is_active'), 'departments', ['is_active'], unique=False)
    
    # Insert some default departments
    op.execute("""
        INSERT INTO departments (name, code, description, is_active) VALUES
        ('技术部', 'TECH', '负责系统开发和技术支持', true),
        ('运维部', 'OPS', '负责系统运维和基础设施管理', true),
        ('产品部', 'PRODUCT', '负责产品规划和设计', true),
        ('市场部', 'MARKETING', '负责市场推广和品牌建设', true),
        ('人事部', 'HR', '负责人力资源管理', true),
        ('财务部', 'FINANCE', '负责财务管理和会计核算', true),
        ('客服部', 'SERVICE', '负责客户服务和支持', true)
    """)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_departments_is_active'), table_name='departments')
    op.drop_index(op.f('ix_departments_code'), table_name='departments')
    op.drop_index(op.f('ix_departments_name'), table_name='departments')
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    
    # Drop table
    op.drop_table('departments')