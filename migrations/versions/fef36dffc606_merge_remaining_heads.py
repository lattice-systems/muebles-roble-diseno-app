"""merge remaining heads

Revision ID: fef36dffc606
Revises: 80c632fe6884, e7b4eae2954e
Create Date: 2026-03-29 18:00:16.875638

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "fef36dffc606"
down_revision = ("80c632fe6884", "e7b4eae2954e")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
