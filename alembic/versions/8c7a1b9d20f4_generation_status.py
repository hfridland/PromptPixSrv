"""Track background generation status.

Revision ID: 8c7a1b9d20f4
Revises: 74ad5c2d8b01
"""
from alembic import op
import sqlalchemy as sa
revision = "8c7a1b9d20f4"
down_revision = "74ad5c2d8b01"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("tree_body", sa.Column("generation_status", sa.String(20), nullable=False, server_default="completed"))
    op.add_column("tree_body", sa.Column("generation_error", sa.String(500), nullable=True))
    op.execute("UPDATE tree_body SET generation_status = 'failed', generation_error = 'Previous unfinished generation' WHERE image IS NULL")

def downgrade():
    op.drop_column("tree_body", "generation_error")
    op.drop_column("tree_body", "generation_status")
