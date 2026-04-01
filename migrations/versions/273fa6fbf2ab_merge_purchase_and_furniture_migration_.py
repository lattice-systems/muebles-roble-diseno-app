"""merge purchase and furniture migration heads

Revision ID: 273fa6fbf2ab
Revises: 4a0f5f6b9c21, fb32db85d5be
Create Date: 2026-03-29 02:31:49.500312

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "273fa6fbf2ab"
down_revision = ("4a0f5f6b9c21", "fb32db85d5be")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
