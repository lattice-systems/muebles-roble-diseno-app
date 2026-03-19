"""add fs_uniquifier to users for flask-security

Revision ID: a04ac2e92cd3
Revises: 4f8c2a9e3b1d
Create Date: 2026-03-18 13:05:44.829841

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a04ac2e92cd3"
down_revision = "4f8c2a9e3b1d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("fs_uniquifier", sa.String(length=64), nullable=True)
    )
    op.execute(
        "UPDATE users SET fs_uniquifier = REPLACE(UUID(), '-', '') "
        "WHERE fs_uniquifier IS NULL"
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "fs_uniquifier", existing_type=sa.String(length=64), nullable=False
        )
        batch_op.create_unique_constraint("uq_users_fs_uniquifier", ["fs_uniquifier"])


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("uq_users_fs_uniquifier", type_="unique")
        batch_op.drop_column("fs_uniquifier")
