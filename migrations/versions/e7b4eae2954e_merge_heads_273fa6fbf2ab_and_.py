"""merge heads 273fa6fbf2ab and b05f91ac862b

Revision ID: e7b4eae2954e
Revises: 273fa6fbf2ab, b05f91ac862b
Create Date: 2026-03-29 04:08:04.112077

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e7b4eae2954e"
down_revision = ("273fa6fbf2ab", "b05f91ac862b")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
