"""merge heads 4fb1f037c349 and 96af9c9fa783

Revision ID: 3a23a3f1d00d
Revises: 4fb1f037c349, 96af9c9fa783
Create Date: 2026-04-04 12:31:19.763531

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3a23a3f1d00d"
down_revision = ("4fb1f037c349", "96af9c9fa783")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
