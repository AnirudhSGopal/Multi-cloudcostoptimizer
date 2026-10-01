"""Add scan coverage metadata and per-job Gemini review consent."""
from alembic import op
import sqlalchemy as sa


revision = "60f8a3d42b91"
down_revision = "ba318b8f0548"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "scan_jobs",
        sa.Column(
            "gemini_review_requested",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "scan_results",
        sa.Column(
            "coverage",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    op.alter_column(
        "scan_results",
        "security_score",
        existing_type=sa.Float(),
        nullable=True,
    )
    op.execute("UPDATE scan_results SET security_score = NULL")
    op.alter_column(
        "scan_jobs",
        "gemini_review_requested",
        server_default=None,
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "scan_results",
        "coverage",
        server_default=None,
        existing_type=sa.JSON(),
        existing_nullable=False,
    )


def downgrade():
    op.drop_column("scan_results", "coverage")
    op.drop_column("scan_jobs", "gemini_review_requested")
