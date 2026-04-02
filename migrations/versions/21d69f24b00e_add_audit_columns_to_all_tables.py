"""add_audit_columns_to_all_tables

Revision ID: 21d69f24b00e
Revises: 9f1b2c3d4e5f
Create Date: 2026-03-31 22:45:23.162915

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "21d69f24b00e"
down_revision = "9f1b2c3d4e5f"
branch_labels = None
depends_on = None


CURRENT_TS = sa.text("CURRENT_TIMESTAMP")

# Keep migration idempotent for environments where some columns/FKs
# were added manually or by partially executed migrations.
AUDIT_PLAN = {
    "bom": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "colors": [
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "customers": [
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "furniture_types": [
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "material_categories": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "orders": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "payment_methods": [
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "payments": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "product_images": [
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "product_inventory": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "production_orders": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "products": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "purchase_orders": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "raw_material_movements": [
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "raw_materials": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "roles": [
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "sales": [
        sa.Column(
            "created_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "suppliers": [
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "units": [
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "users": [
        sa.Column(
            "updated_at", sa.DateTime(), server_default=CURRENT_TS, nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
    "wood_types": [
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
    ],
}

AUDIT_FK_COLUMNS = {"created_by", "updated_by", "deactivated_by"}


def _existing_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _existing_user_fk_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    result = set()
    for fk in inspector.get_foreign_keys(table_name):
        constrained = fk.get("constrained_columns") or []
        referred_table = fk.get("referred_table")
        referred_columns = fk.get("referred_columns") or []
        if (
            referred_table == "users"
            and len(constrained) == 1
            and referred_columns == ["id"]
        ):
            result.add(constrained[0])
    return result


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name, columns in AUDIT_PLAN.items():
        existing_cols = _existing_columns(inspector, table_name)
        existing_fk_cols = _existing_user_fk_columns(inspector, table_name)

        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for column in columns:
                if column.name not in existing_cols:
                    batch_op.add_column(column)
                    existing_cols.add(column.name)

            for fk_column in AUDIT_FK_COLUMNS:
                if fk_column in existing_cols and fk_column not in existing_fk_cols:
                    batch_op.create_foreign_key(
                        None,
                        "users",
                        [fk_column],
                        ["id"],
                    )


def downgrade():
    # Intentionally left as no-op.
    # This migration is now idempotent to safely recover inconsistent
    # environments where audit fields were partially applied.
    pass
