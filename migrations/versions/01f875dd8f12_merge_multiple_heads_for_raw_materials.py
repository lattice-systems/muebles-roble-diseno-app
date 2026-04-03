"""Merge multiple heads for raw_materials

Revision ID: 01f875dd8f12
Revises: 4a0f5f6b9c21, b05f91ac862b
Create Date: 2026-03-29 16:47:11.881059

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "01f875dd8f12"
down_revision = ("4a0f5f6b9c21", "b05f91ac862b")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
