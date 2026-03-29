"""Merge all heads

Revision ID: 80c632fe6884
Revises: 4a0f5f6b9c21, 4acdc2073fe4, b05f91ac862b
Create Date: 2026-03-29 13:43:41.936504

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "80c632fe6884"
down_revision = ("4a0f5f6b9c21", "4acdc2073fe4", "b05f91ac862b")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
