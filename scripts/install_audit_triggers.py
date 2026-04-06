"""Instala triggers MySQL de auditoria para todas las tablas de negocio."""

from __future__ import annotations

import hashlib
import os
import sys

import sqlalchemy as sa

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

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


def _build_trigger_sql(inspector: sa.Inspector, table_name: str) -> list[str]:
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

    return [
        f"DROP TRIGGER IF EXISTS `{trigger_insert}`",
        f"""
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
""",
        f"DROP TRIGGER IF EXISTS `{trigger_update}`",
        f"""
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
""",
        f"DROP TRIGGER IF EXISTS `{trigger_delete}`",
        f"""
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
""",
    ]


def main() -> None:
    app = create_app()

    with app.app_context():
        with db.engine.begin() as connection:
            if connection.dialect.name != "mysql":
                raise RuntimeError(
                    "Este instalador de auditoria solo aplica para MySQL. "
                    f"Dialect actual: {connection.dialect.name}"
                )

            inspector = sa.inspect(connection)
            if "audit_log" not in inspector.get_table_names():
                raise RuntimeError(
                    "No existe la tabla audit_log. Ejecuta primero flask db upgrade."
                )

            audit_columns = {c["name"] for c in inspector.get_columns("audit_log")}
            required_columns = {"record_id", "source"}
            missing = sorted(required_columns - audit_columns)
            if missing:
                raise RuntimeError(
                    "Faltan columnas en audit_log: "
                    f"{', '.join(missing)}. Ejecuta flask db upgrade."
                )

            tables = _tables_to_audit(inspector)
            for table_name in tables:
                statements = _build_trigger_sql(inspector, table_name)
                for statement in statements:
                    connection.execute(sa.text(statement))

            print(
                f"Triggers de auditoria instalados correctamente para {len(tables)} tablas."
            )


if __name__ == "__main__":
    main()
