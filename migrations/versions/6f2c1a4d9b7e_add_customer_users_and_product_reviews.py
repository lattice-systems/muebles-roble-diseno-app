"""Add customer users and product reviews

Revision ID: 6f2c1a4d9b7e
Revises: 01984e5915f5
Create Date: 2026-04-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6f2c1a4d9b7e"
down_revision = "01984e5915f5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("fs_uniquifier", sa.String(length=64), nullable=False),
        sa.Column("tf_primary_method", sa.String(length=64), nullable=True),
        sa.Column("tf_totp_secret", sa.String(length=255), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_customer_users_email"),
        sa.UniqueConstraint("fs_uniquifier", name="uq_customer_users_fs_uniquifier"),
    )
    op.create_index("ix_customer_users_email", "customer_users", ["email"], unique=True)

    op.add_column("customers", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_customers_user_id", "customers", ["user_id"])
    op.create_foreign_key(
        "fk_customers_user_id_customer_users",
        "customers",
        "customer_users",
        ["user_id"],
        ["id"],
    )

    op.add_column("orders", sa.Column("customer_user_id", sa.Integer(), nullable=True))
    op.create_index("ix_orders_customer_user_id", "orders", ["customer_user_id"])
    op.create_foreign_key(
        "fk_orders_customer_user_id_customer_users",
        "orders",
        "customer_users",
        ["customer_user_id"],
        ["id"],
    )

    op.create_table(
        "product_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("customer_user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_product_reviews_rating"
        ),
        sa.ForeignKeyConstraint(["customer_user_id"], ["customer_users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "customer_user_id",
            name="uq_product_reviews_product_customer_user",
        ),
    )
    op.create_index(
        "ix_product_reviews_customer_user_id",
        "product_reviews",
        ["customer_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_reviews_product_id",
        "product_reviews",
        ["product_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_product_reviews_product_id", table_name="product_reviews")
    op.drop_index("ix_product_reviews_customer_user_id", table_name="product_reviews")
    op.drop_table("product_reviews")

    op.drop_constraint(
        "fk_orders_customer_user_id_customer_users",
        "orders",
        type_="foreignkey",
    )
    op.drop_index("ix_orders_customer_user_id", table_name="orders")
    op.drop_column("orders", "customer_user_id")

    op.drop_constraint(
        "fk_customers_user_id_customer_users", "customers", type_="foreignkey"
    )
    op.drop_constraint("uq_customers_user_id", "customers", type_="unique")
    op.drop_column("customers", "user_id")

    op.drop_index("ix_customer_users_email", table_name="customer_users")
    op.drop_table("customer_users")
