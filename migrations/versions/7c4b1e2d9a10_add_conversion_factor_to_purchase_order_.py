"""add conversion_factor to purchase_order_items

Revision ID: 7c4b1e2d9a10
Revises: 3a23a3f1d00d
Create Date: 2026-04-04 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7c4b1e2d9a10"
down_revision = "3a23a3f1d00d"
branch_labels = None
depends_on = None


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "purchase_order_items", "conversion_factor"):
        with op.batch_alter_table("purchase_order_items", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "conversion_factor",
                    sa.Numeric(precision=12, scale=3),
                    nullable=False,
                    server_default=sa.text("1.000"),
                )
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _column_exists(inspector, "purchase_order_items", "conversion_factor"):
        with op.batch_alter_table("purchase_order_items", schema=None) as batch_op:
            batch_op.drop_column("conversion_factor")
