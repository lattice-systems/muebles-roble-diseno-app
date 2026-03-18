"""add two-factor columns to users

Revision ID: 8b98bc0a9380
Revises: a04ac2e92cd3
Create Date: 2026-03-18 13:38:39.542649

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8b98bc0a9380"
down_revision = "a04ac2e92cd3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("tf_primary_method", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "users", sa.Column("tf_totp_secret", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "users", sa.Column("tf_phone_number", sa.String(length=128), nullable=True)
    )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("tf_phone_number")
        batch_op.drop_column("tf_totp_secret")
        batch_op.drop_column("tf_primary_method")
