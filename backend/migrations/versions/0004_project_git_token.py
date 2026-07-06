"""project git token for private repos

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("git_token_encrypted", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "git_token_encrypted")
