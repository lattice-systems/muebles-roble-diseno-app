"""update product_image model with columns for cloudinary

Revision ID: 4fb1f037c349
Revises: c4f2a8b7d901
Create Date: 2026-04-03 11:51:09.318603

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "4fb1f037c349"
down_revision = "c4f2a8b7d901"
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

    # Remove legacy order audit constraints/columns only when present.
    for fk_name in ("orders_ibfk_5", "orders_ibfk_4", "orders_ibfk_3"):
        if _fk_exists(inspector, "orders", fk_name):
            op.drop_constraint(fk_name, "orders", type_="foreignkey")

    inspector = sa.inspect(bind)
    for column_name in (
        "deactivated_at",
        "updated_at",
        "updated_by",
        "created_at",
        "created_by",
        "deactivated_by",
    ):
        if _column_exists(inspector, "orders", column_name):
            op.drop_column("orders", column_name)

    inspector = sa.inspect(bind)
    image_url_exists = _column_exists(inspector, "product_images", "image_url")
    image_path_exists = _column_exists(inspector, "product_images", "image_path")

    if not image_url_exists and image_path_exists:
        op.alter_column(
            "product_images",
            "image_path",
            new_column_name="image_url",
            existing_type=sa.String(length=255),
            type_=sa.String(length=500),
            existing_nullable=False,
            nullable=True,
        )
    elif image_url_exists:
        op.alter_column(
            "product_images",
            "image_url",
            existing_type=mysql.VARCHAR(length=500),
            nullable=True,
        )
    else:
        op.add_column(
            "product_images",
            sa.Column("image_url", sa.String(length=500), nullable=True),
        )

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "product_images", "public_id"):
        op.alter_column(
            "product_images",
            "public_id",
            existing_type=mysql.VARCHAR(length=255),
            nullable=True,
        )
    else:
        op.add_column(
            "product_images",
            sa.Column("public_id", sa.String(length=255), nullable=True),
        )

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "product_images", "sort_order"):
        op.alter_column(
            "product_images",
            "sort_order",
            existing_type=mysql.INTEGER(),
            nullable=True,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _column_exists(inspector, "product_images", "sort_order"):
        op.alter_column(
            "product_images",
            "sort_order",
            existing_type=mysql.INTEGER(),
            nullable=False,
        )

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "product_images", "public_id"):
        op.alter_column(
            "product_images",
            "public_id",
            existing_type=mysql.VARCHAR(length=255),
            nullable=False,
        )

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "product_images", "image_url"):
        op.alter_column(
            "product_images",
            "image_url",
            existing_type=mysql.VARCHAR(length=500),
            nullable=False,
        )

    inspector = sa.inspect(bind)
    for column_name, column in (
        ("deactivated_by", sa.Column("deactivated_by", mysql.INTEGER(), nullable=True)),
        ("created_by", sa.Column("created_by", mysql.INTEGER(), nullable=True)),
        (
            "created_at",
            sa.Column(
                "created_at",
                mysql.DATETIME(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        ),
        ("updated_by", sa.Column("updated_by", mysql.INTEGER(), nullable=True)),
        (
            "updated_at",
            sa.Column(
                "updated_at",
                mysql.DATETIME(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        ),
        (
            "deactivated_at",
            sa.Column("deactivated_at", mysql.DATETIME(), nullable=True),
        ),
    ):
        if not _column_exists(inspector, "orders", column_name):
            op.add_column("orders", column)
            inspector = sa.inspect(bind)

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "deactivated_by") and not _fk_exists(
        inspector, "orders", "orders_ibfk_3"
    ):
        op.create_foreign_key(
            "orders_ibfk_3", "orders", "users", ["deactivated_by"], ["id"]
        )

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "created_by") and not _fk_exists(
        inspector, "orders", "orders_ibfk_4"
    ):
        op.create_foreign_key(
            "orders_ibfk_4", "orders", "users", ["created_by"], ["id"]
        )

    inspector = sa.inspect(bind)
    if _column_exists(inspector, "orders", "updated_by") and not _fk_exists(
        inspector, "orders", "orders_ibfk_5"
    ):
        op.create_foreign_key(
            "orders_ibfk_5", "orders", "users", ["updated_by"], ["id"]
        )
