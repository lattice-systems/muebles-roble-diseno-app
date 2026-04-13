"""Add assigned user to production orders.

Revision ID: d2f8a5c1b7e4
Revises: b6d4f9a1c2e3
Create Date: 2026-04-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d2f8a5c1b7e4"
down_revision = "b6d4f9a1c2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "production_orders" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("production_orders")}
    if "assigned_user_id" not in columns:
        op.add_column(
            "production_orders",
            sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        )

    inspector = sa.inspect(bind)
    fk_names = {
        fk.get("name")
        for fk in inspector.get_foreign_keys("production_orders")
        if fk.get("name")
    }
    fk_name = "fk_production_orders_assigned_user_id_users"
    if fk_name not in fk_names:
        op.create_foreign_key(
            fk_name,
            "production_orders",
            "users",
            ["assigned_user_id"],
            ["id"],
        )

    index_names = {
        idx.get("name")
        for idx in inspector.get_indexes("production_orders")
        if idx.get("name")
    }
    index_name = "ix_production_orders_assigned_user_id"
    if index_name not in index_names:
        op.create_index(
            index_name,
            "production_orders",
            ["assigned_user_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "production_orders" not in inspector.get_table_names():
        return

    index_names = {
        idx.get("name")
        for idx in inspector.get_indexes("production_orders")
        if idx.get("name")
    }
    index_name = "ix_production_orders_assigned_user_id"
    if index_name in index_names:
        op.drop_index(index_name, table_name="production_orders")

    fk_names = {
        fk.get("name")
        for fk in inspector.get_foreign_keys("production_orders")
        if fk.get("name")
    }
    fk_name = "fk_production_orders_assigned_user_id_users"
    if fk_name in fk_names:
        op.drop_constraint(fk_name, "production_orders", type_="foreignkey")

    columns = {col["name"] for col in inspector.get_columns("production_orders")}
    if "assigned_user_id" in columns:
        op.drop_column("production_orders", "assigned_user_id")
