"""add_audit_trigger_module_and_log_fields

Revision ID: 6d0f4b7e2a91
Revises: 3f9a8d2c7b11
Create Date: 2026-04-05 10:30:00.000000

"""

from __future__ import annotations

import hashlib

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6d0f4b7e2a91"
down_revision = "3f9a8d2c7b11"
branch_labels = None
depends_on = None

EXCLUDED_AUDIT_TABLES = {"audit_log", "alembic_version"}
USER_HINT_COLUMNS = (
    "updated_by",
    "created_by",
    "deactivated_by",
    "created_by_id",
    "cancelled_by_id",
    "id_employee",
    "user_id",
)


def _trigger_name(table_name: str, suffix: str) -> str:
    base = f"trg_audit_{table_name}_{suffix}"
    if len(base) <= 64:
        return base

    digest = hashlib.md5(table_name.encode("utf-8")).hexdigest()[:6]
    remaining = 64 - len(f"trg_audit__{suffix}_{digest}")
    table_part = table_name[:remaining]
    return f"trg_audit_{table_part}_{suffix}_{digest}"


def _table_columns(inspector: sa.Inspector, table_name: str) -> list[str]:
    return [column["name"] for column in inspector.get_columns(table_name)]


def _table_column_set(inspector: sa.Inspector, table_name: str) -> set[str]:
    return set(_table_columns(inspector, table_name))


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {
        index["name"]
        for index in inspector.get_indexes(table_name)
        if index.get("name")
    }


def _primary_key_column(inspector: sa.Inspector, table_name: str) -> str | None:
    pk = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
    return pk[0] if pk else None


def _json_row_expression(columns: list[str], row_alias: str) -> str:
    if not columns:
        return "JSON_OBJECT()"

    items: list[str] = []
    for column in columns:
        escaped = column.replace("`", "``")
        items.append(f"'{escaped}'")
        items.append(f"{row_alias}.`{escaped}`")

    return "JSON_OBJECT(" + ", ".join(items) + ")"


def _user_expression(columns: set[str], aliases: tuple[str, ...]) -> str:
    candidates = ["@audit_user_id"]

    for alias in aliases:
        for column in USER_HINT_COLUMNS:
            if column in columns:
                escaped = column.replace("`", "``")
                candidates.append(f"{alias}.`{escaped}`")

    return "COALESCE(" + ", ".join(candidates) + ")"


def _record_expression(pk_column: str | None, row_alias: str) -> str:
    if not pk_column:
        return "NULL"

    escaped = pk_column.replace("`", "``")
    return f"CAST({row_alias}.`{escaped}` AS CHAR)"


def _tables_to_audit(inspector: sa.Inspector) -> list[str]:
    return sorted(
        table_name
        for table_name in inspector.get_table_names()
        if table_name not in EXCLUDED_AUDIT_TABLES
    )


def _create_mysql_audit_triggers(inspector: sa.Inspector) -> None:
    for table_name in _tables_to_audit(inspector):
        columns = _table_columns(inspector, table_name)
        columns_set = set(columns)
        pk_column = _primary_key_column(inspector, table_name)

        json_new = _json_row_expression(columns, "NEW")
        json_old = _json_row_expression(columns, "OLD")

        user_insert = _user_expression(columns_set, ("NEW",))
        user_update = _user_expression(columns_set, ("NEW", "OLD"))
        user_delete = _user_expression(columns_set, ("OLD",))

        record_new = _record_expression(pk_column, "NEW")
        record_old = _record_expression(pk_column, "OLD")

        trigger_insert = _trigger_name(table_name, "ai")
        trigger_update = _trigger_name(table_name, "au")
        trigger_delete = _trigger_name(table_name, "ad")

        op.execute(f"DROP TRIGGER IF EXISTS `{trigger_insert}`")
        op.execute(f"""
CREATE TRIGGER `{trigger_insert}`
AFTER INSERT ON `{table_name}`
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (
        table_name,
        action,
        user_id,
        timestamp,
        previous_data,
        new_data,
        record_id,
        source
    )
    VALUES (
        '{table_name}',
        'INSERT',
        {user_insert},
        NOW(),
        NULL,
        {json_new},
        {record_new},
        'db_trigger'
    );
END
""")

        op.execute(f"DROP TRIGGER IF EXISTS `{trigger_update}`")
        op.execute(f"""
CREATE TRIGGER `{trigger_update}`
AFTER UPDATE ON `{table_name}`
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (
        table_name,
        action,
        user_id,
        timestamp,
        previous_data,
        new_data,
        record_id,
        source
    )
    VALUES (
        '{table_name}',
        'UPDATE',
        {user_update},
        NOW(),
        {json_old},
        {json_new},
        COALESCE({record_new}, {record_old}),
        'db_trigger'
    );
END
""")

        op.execute(f"DROP TRIGGER IF EXISTS `{trigger_delete}`")
        op.execute(f"""
CREATE TRIGGER `{trigger_delete}`
AFTER DELETE ON `{table_name}`
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (
        table_name,
        action,
        user_id,
        timestamp,
        previous_data,
        new_data,
        record_id,
        source
    )
    VALUES (
        '{table_name}',
        'DELETE',
        {user_delete},
        NOW(),
        {json_old},
        NULL,
        {record_old},
        'db_trigger'
    );
END
""")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "audit_log" not in inspector.get_table_names():
        return

    existing_columns = _table_column_set(inspector, "audit_log")

    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        if "record_id" not in existing_columns:
            batch_op.add_column(
                sa.Column("record_id", sa.String(length=100), nullable=True)
            )

        if "source" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "source",
                    sa.String(length=30),
                    nullable=False,
                    server_default=sa.text("'application'"),
                )
            )

    inspector = sa.inspect(bind)
    existing_indexes = _index_names(inspector, "audit_log")

    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        if "ix_audit_log_timestamp" not in existing_indexes:
            batch_op.create_index("ix_audit_log_timestamp", ["timestamp"], unique=False)

        if "ix_audit_log_table_timestamp" not in existing_indexes:
            batch_op.create_index(
                "ix_audit_log_table_timestamp",
                ["table_name", "timestamp"],
                unique=False,
            )

        if "ix_audit_log_user_timestamp" not in existing_indexes:
            batch_op.create_index(
                "ix_audit_log_user_timestamp", ["user_id", "timestamp"], unique=False
            )

    if bind.dialect.name != "mysql":
        return

    inspector = sa.inspect(bind)
    _create_mysql_audit_triggers(inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if bind.dialect.name == "mysql":
        for table_name in _tables_to_audit(inspector):
            op.execute(f"DROP TRIGGER IF EXISTS `{_trigger_name(table_name, 'ai')}`")
            op.execute(f"DROP TRIGGER IF EXISTS `{_trigger_name(table_name, 'au')}`")
            op.execute(f"DROP TRIGGER IF EXISTS `{_trigger_name(table_name, 'ad')}`")

    if "audit_log" not in inspector.get_table_names():
        return

    existing_indexes = _index_names(inspector, "audit_log")
    existing_columns = _table_column_set(inspector, "audit_log")

    with op.batch_alter_table("audit_log", schema=None) as batch_op:
        if "ix_audit_log_user_timestamp" in existing_indexes:
            batch_op.drop_index("ix_audit_log_user_timestamp")

        if "ix_audit_log_table_timestamp" in existing_indexes:
            batch_op.drop_index("ix_audit_log_table_timestamp")

        if "ix_audit_log_timestamp" in existing_indexes:
            batch_op.drop_index("ix_audit_log_timestamp")

        if "source" in existing_columns:
            batch_op.drop_column("source")

        if "record_id" in existing_columns:
            batch_op.drop_column("record_id")
