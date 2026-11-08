"""Persist image AI provider.

Revision ID: 9e20b7d4a621
Revises: 8c7a1b9d20f4
"""
from alembic import op
import sqlalchemy as sa
revision = "9e20b7d4a621"
down_revision = "8c7a1b9d20f4"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("tree_body", sa.Column("ai_provider", sa.String(30), nullable=True))
    op.execute("UPDATE tree_body SET ai_provider = 'OpenAI' WHERE parent_id IS NOT NULL")

def downgrade():
    op.drop_column("tree_body", "ai_provider")
