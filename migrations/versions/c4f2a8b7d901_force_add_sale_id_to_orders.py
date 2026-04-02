"""force add sale_id to orders

Revision ID: c4f2a8b7d901
Revises: b3e1f0d9c2a7
Create Date: 2026-04-02 12:45:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c4f2a8b7d901"
down_revision = "b3e1f0d9c2a7"
branch_labels = None
depends_on = None


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def _fk_exists(inspector, table_name: str, constraint_name: str) -> bool:
    return constraint_name in {
        fk.get("name")
        for fk in inspector.get_foreign_keys(table_name)
        if fk.get("name")
    }


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "orders", "sale_id"):
        op.add_column("orders", sa.Column("sale_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "sale_id") and not _fk_exists(
        inspector, "orders", "fk_orders_sale_id"
    ):
        op.create_foreign_key(
            "fk_orders_sale_id", "orders", "sales", ["sale_id"], ["id"]
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _fk_exists(inspector, "orders", "fk_orders_sale_id"):
        op.drop_constraint("fk_orders_sale_id", "orders", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "sale_id"):
        op.drop_column("orders", "sale_id")
