"""hashed_password nullable for SSO-provisioned users

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-09

"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    # An empty hash never verifies, so former SSO users simply cannot log in
    # with a password (instead of being deleted and losing their audit trail).
    op.execute("UPDATE users SET hashed_password = '' WHERE hashed_password IS NULL")
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=False)
