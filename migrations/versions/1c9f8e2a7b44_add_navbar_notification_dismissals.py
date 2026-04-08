"""add_navbar_notification_dismissals

Revision ID: 1c9f8e2a7b44
Revises: 7e11c2a8f4d2
Create Date: 2026-04-05 22:40:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1c9f8e2a7b44"
down_revision = "7e11c2a8f4d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "navbar_notification_dismissals" not in inspector.get_table_names():
        op.create_table(
            "navbar_notification_dismissals",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("source_kind", sa.String(length=20), nullable=False),
            sa.Column("source_id", sa.Integer(), nullable=False),
            sa.Column(
                "dismissed_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "source_kind",
                "source_id",
                name="uq_navbar_notification_dismissal_user_source",
            ),
        )

    inspector = sa.inspect(bind)
    index_names = {
        index["name"]
        for index in inspector.get_indexes("navbar_notification_dismissals")
        if index.get("name")
    }

    with op.batch_alter_table(
        "navbar_notification_dismissals", schema=None
    ) as batch_op:
        if "ix_navbar_notification_dismissals_user_timestamp" not in index_names:
            batch_op.create_index(
                "ix_navbar_notification_dismissals_user_timestamp",
                ["user_id", "dismissed_at"],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "navbar_notification_dismissals" not in inspector.get_table_names():
        return

    index_names = {
        index["name"]
        for index in inspector.get_indexes("navbar_notification_dismissals")
        if index.get("name")
    }

    with op.batch_alter_table(
        "navbar_notification_dismissals", schema=None
    ) as batch_op:
        if "ix_navbar_notification_dismissals_user_timestamp" in index_names:
            batch_op.drop_index("ix_navbar_notification_dismissals_user_timestamp")

    op.drop_table("navbar_notification_dismissals")
