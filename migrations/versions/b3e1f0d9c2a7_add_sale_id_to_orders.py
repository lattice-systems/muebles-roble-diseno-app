"""add sale_id to orders

Revision ID: b3e1f0d9c2a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02 12:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b3e1f0d9c2a7"
down_revision = "a1b2c3d4e5f6"
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
        with op.batch_alter_table("orders", schema=None) as batch_op:
            batch_op.add_column(sa.Column("sale_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "sale_id") and not _fk_exists(
        inspector, "orders", "fk_orders_sale_id"
    ):
        with op.batch_alter_table("orders", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_orders_sale_id", "sales", ["sale_id"], ["id"]
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _fk_exists(inspector, "orders", "fk_orders_sale_id"):
        with op.batch_alter_table("orders", schema=None) as batch_op:
            batch_op.drop_constraint("fk_orders_sale_id", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "sale_id"):
        with op.batch_alter_table("orders", schema=None) as batch_op:
            batch_op.drop_column("sale_id")
