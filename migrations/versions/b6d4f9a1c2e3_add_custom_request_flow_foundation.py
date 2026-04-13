"""Add custom request flow foundation

Revision ID: b6d4f9a1c2e3
Revises: 6f2c1a4d9b7e
Create Date: 2026-04-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b6d4f9a1c2e3"
down_revision = "6f2c1a4d9b7e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "furniture_types",
        sa.Column(
            "requires_contact_request",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "is_special_request",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "is_special_request",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "production_orders",
        sa.Column(
            "is_special_request",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "production_orders",
        sa.Column(
            "do_not_add_to_finished_stock",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "production_orders",
        sa.Column("special_notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "contact_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("subject", sa.String(length=180), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "request_type",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'custom_furniture'"),
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'new'"),
        ),
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'ecommerce'"),
        ),
        sa.Column("preferred_datetime", sa.DateTime(), nullable=True),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("customer_user_id", sa.Integer(), nullable=True),
        sa.Column("converted_order_id", sa.Integer(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
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
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("deactivated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["customer_user_id"], ["customer_users.id"]),
        sa.ForeignKeyConstraint(["converted_order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["deactivated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_contact_requests_email",
        "contact_requests",
        ["email"],
        unique=False,
    )
    op.create_index(
        "ix_contact_requests_status",
        "contact_requests",
        ["status"],
        unique=False,
    )

    # Mantener la categoría oficial de personalizados en modo contacto.
    op.execute("""
        UPDATE furniture_types
        SET requires_contact_request = 1
        WHERE slug = 'muebles-personalizados'
           OR LOWER(title) = 'muebles personalizados'
        """)


def downgrade():
    op.drop_index("ix_contact_requests_status", table_name="contact_requests")
    op.drop_index("ix_contact_requests_email", table_name="contact_requests")
    op.drop_table("contact_requests")

    op.drop_column("production_orders", "special_notes")
    op.drop_column("production_orders", "do_not_add_to_finished_stock")
    op.drop_column("production_orders", "is_special_request")
    op.drop_column("orders", "is_special_request")
    op.drop_column("products", "is_special_request")
    op.drop_column("furniture_types", "requires_contact_request")
