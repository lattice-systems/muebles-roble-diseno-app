"""merge branches

Revision ID: 8bc17c08e447
Revises: 1c9f8e2a7b44, cd5b2b0fdde9
Create Date: 2026-04-06 00:47:11.430765

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8bc17c08e447"
down_revision = ("1c9f8e2a7b44", "cd5b2b0fdde9")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
