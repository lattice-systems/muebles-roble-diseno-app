"""RawMaterials_v2

Revision ID: 96af9c9fa783
Revises: 01f875dd8f12
Create Date: 2026-03-29 16:48:01.059677

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "96af9c9fa783"
down_revision = "01f875dd8f12"
branch_labels = None
depends_on = None


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def _fk_exists_for_column(
    inspector, table_name: str, referred_table: str, local_column: str
) -> bool:
    for fk in inspector.get_foreign_keys(table_name):
        constrained = fk.get("constrained_columns") or []
        referred = fk.get("referred_table")
        if referred == referred_table and local_column in constrained:
            return True
    return False


def _fk_name_for_column(inspector, table_name: str, local_column: str):
    for fk in inspector.get_foreign_keys(table_name):
        constrained = fk.get("constrained_columns") or []
        if local_column in constrained and fk.get("name"):
            return fk.get("name")
    return None


def _fk_names_for_column(inspector, table_name: str, local_column: str):
    names = []
    for fk in inspector.get_foreign_keys(table_name):
        constrained = fk.get("constrained_columns") or []
        name = fk.get("name")
        if local_column in constrained and name:
            names.append(name)
    return names


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "raw_materials", "created_at"):
        op.add_column(
            "raw_materials",
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

    inspector = sa.inspect(bind)
    if not _column_exists(inspector, "raw_materials", "updated_at"):
        op.add_column(
            "raw_materials",
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

    inspector = sa.inspect(bind)
    if not _fk_exists_for_column(
        inspector, "raw_materials", "material_categories", "category_id"
    ):
        op.create_foreign_key(
            "fk_raw_materials_category_id",
            "raw_materials",
            "material_categories",
            ["category_id"],
            ["id"],
        )

    inspector = sa.inspect(bind)
    for fk_name in _fk_names_for_column(inspector, "raw_materials", "supplier_id"):
        op.drop_constraint(fk_name, "raw_materials", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "raw_materials", "supplier_id"):
        op.drop_column("raw_materials", "supplier_id")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "raw_materials", "estimated_cost"):
        op.drop_column("raw_materials", "estimated_cost")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _column_exists(inspector, "raw_materials", "estimated_cost"):
        op.add_column(
            "raw_materials",
            sa.Column(
                "estimated_cost", mysql.DECIMAL(precision=12, scale=2), nullable=True
            ),
        )

    inspector = sa.inspect(bind)
    if not _column_exists(inspector, "raw_materials", "supplier_id"):
        op.add_column(
            "raw_materials",
            sa.Column(
                "supplier_id", mysql.INTEGER(), autoincrement=False, nullable=True
            ),
        )

    inspector = sa.inspect(bind)
    fk_name = _fk_name_for_column(inspector, "raw_materials", "category_id")
    if fk_name:
        op.drop_constraint(fk_name, "raw_materials", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "raw_materials", "updated_at"):
        op.drop_column("raw_materials", "updated_at")

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "raw_materials", "created_at"):
        op.drop_column("raw_materials", "created_at")
