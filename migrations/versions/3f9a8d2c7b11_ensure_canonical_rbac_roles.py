"""ensure canonical rbac roles

Revision ID: 3f9a8d2c7b11
Revises: 7c4b1e2d9a10
Create Date: 2026-04-05 15:35:00.000000

"""

from __future__ import annotations

import unicodedata

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3f9a8d2c7b11"
down_revision = "7c4b1e2d9a10"
branch_labels = None
depends_on = None


CANONICAL_ROLES = [
    (
        "Administrador",
        "Acceso total al sistema, configuración y administración global.",
    ),
    (
        "Producción",
        "Operación de producción, BOM, inventario y módulos operativos asignados.",
    ),
    (
        "Ventas",
        "Operación comercial, POS, órdenes de cliente y consulta operativa.",
    ),
    (
        "Cliente",
        "Rol reservado para capacidades de usuario final en canales de cliente.",
    ),
]


def _normalize_role_name(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().strip().split())


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "roles" not in inspector.get_table_names():
        return

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("status", sa.Boolean),
    )

    existing_rows = bind.execute(
        sa.select(roles_table.c.id, roles_table.c.name, roles_table.c.description)
    ).all()
    existing_by_normalized = {
        _normalize_role_name(row.name): row for row in existing_rows
    }

    for role_name, default_description in CANONICAL_ROLES:
        normalized_name = _normalize_role_name(role_name)
        existing = existing_by_normalized.get(normalized_name)

        if existing is None:
            bind.execute(
                sa.insert(roles_table).values(
                    name=role_name,
                    description=default_description,
                    status=True,
                )
            )
            continue

        existing_description = (existing.description or "").strip()
        if not existing_description and default_description:
            bind.execute(
                sa.update(roles_table)
                .where(roles_table.c.id == existing.id)
                .values(description=default_description)
            )


def downgrade():
    # No-op intencional:
    # esta migración solo asegura existencia de roles base de forma idempotente.
    pass
