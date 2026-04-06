"""add_security_event_log_table

Revision ID: 7e11c2a8f4d2
Revises: 6d0f4b7e2a91
Create Date: 2026-04-05 21:10:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7e11c2a8f4d2"
down_revision = "6d0f4b7e2a91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "security_event_log" not in inspector.get_table_names():
        op.create_table(
            "security_event_log",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column(
                "result",
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'info'"),
            ),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("email_or_identifier", sa.String(length=255), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("context_data", sa.JSON(), nullable=True),
            sa.Column(
                "source",
                sa.String(length=30),
                nullable=False,
                server_default=sa.text("'application'"),
            ),
            sa.Column(
                "timestamp",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(bind)
    index_names = {
        index["name"]
        for index in inspector.get_indexes("security_event_log")
        if index.get("name")
    }

    with op.batch_alter_table("security_event_log", schema=None) as batch_op:
        if "ix_security_event_log_timestamp" not in index_names:
            batch_op.create_index(
                "ix_security_event_log_timestamp", ["timestamp"], unique=False
            )
        if "ix_security_event_log_event_type_timestamp" not in index_names:
            batch_op.create_index(
                "ix_security_event_log_event_type_timestamp",
                ["event_type", "timestamp"],
                unique=False,
            )
        if "ix_security_event_log_user_timestamp" not in index_names:
            batch_op.create_index(
                "ix_security_event_log_user_timestamp",
                ["user_id", "timestamp"],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "security_event_log" not in inspector.get_table_names():
        return

    index_names = {
        index["name"]
        for index in inspector.get_indexes("security_event_log")
        if index.get("name")
    }

    with op.batch_alter_table("security_event_log", schema=None) as batch_op:
        if "ix_security_event_log_user_timestamp" in index_names:
            batch_op.drop_index("ix_security_event_log_user_timestamp")
        if "ix_security_event_log_event_type_timestamp" in index_names:
            batch_op.drop_index("ix_security_event_log_event_type_timestamp")
        if "ix_security_event_log_timestamp" in index_names:
            batch_op.drop_index("ix_security_event_log_timestamp")

    op.drop_table("security_event_log")
