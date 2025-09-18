"""Add readonly role to user enum

Revision ID: 006
Revises: 005
Create Date: 2025-01-09 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'readonly' to the UserRole enum
    # MySQL requires recreating the enum with all values
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'manager', 'user', 'readonly') DEFAULT 'user'")


def downgrade() -> None:
    # Remove 'readonly' from the UserRole enum
    # First, update any existing 'readonly' users to 'user'
    op.execute("UPDATE users SET role = 'user' WHERE role = 'readonly'")
    # Then modify the enum to remove 'readonly'
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'manager', 'user') DEFAULT 'user'")