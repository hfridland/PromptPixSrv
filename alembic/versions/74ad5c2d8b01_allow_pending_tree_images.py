"""Allow child nodes to exist before AI image generation.

Revision ID: 74ad5c2d8b01
Revises: 19ea656566cc
"""
from alembic import op
import sqlalchemy as sa
revision = '74ad5c2d8b01'
down_revision = '19ea656566cc'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('tree_body', 'image', existing_type=sa.LargeBinary(), nullable=True)

def downgrade():
    op.execute('DELETE FROM tree_body WHERE image IS NULL')
    op.alter_column('tree_body', 'image', existing_type=sa.LargeBinary(), nullable=False)
