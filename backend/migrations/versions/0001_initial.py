"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("smtp_host", sa.String(255), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("smtp_username", sa.String(255), nullable=True),
        sa.Column("smtp_password_encrypted", sa.Text(), nullable=True),
        sa.Column("smtp_use_tls", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("smtp_from_address", sa.String(255), nullable=True),
        sa.Column("default_semgrep_config", sa.String(255), nullable=False, server_default="p/default"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_target_type", sa.String(32), nullable=True),
        sa.Column("default_target_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("scan_types", sa.JSON(), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=True),
        sa.Column("target_value", sa.Text(), nullable=True),
        sa.Column("dast_url", sa.Text(), nullable=True),
        sa.Column("dast_full_scan", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("tool_status", sa.JSON(), nullable=False),
        sa.Column("severity_counts", sa.JSON(), nullable=True),
        sa.Column("total_findings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scans_project_id", "scans", ["project_id"])

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_id", sa.Integer(), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool", sa.String(16), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rule_id", sa.String(255), nullable=True),
        sa.Column("cwe", sa.String(32), nullable=True),
        sa.Column("cve", sa.String(64), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("package_name", sa.String(255), nullable=True),
        sa.Column("installed_version", sa.String(128), nullable=True),
        sa.Column("fixed_version", sa.String(128), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("is_new", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
    )
    op.create_index("ix_findings_scan_id", "findings", ["scan_id"])
    op.create_index("ix_findings_fingerprint", "findings", ["fingerprint"])
    op.create_index("ix_findings_scan_severity", "findings", ["scan_id", "severity"])
    op.create_index("ix_findings_scan_tool", "findings", ["scan_id", "tool"])


def downgrade() -> None:
    op.drop_table("findings")
    op.drop_table("scans")
    op.drop_table("projects")
    op.drop_table("app_settings")
    op.drop_table("users")
