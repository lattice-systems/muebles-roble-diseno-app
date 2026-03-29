"""Rename furniture_types.name to title and drop description

Revision ID: 4a0f5f6b9c21
Revises: edc745f354f5
Create Date: 2026-03-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import re

# revision identifiers, used by Alembic.
revision = "4a0f5f6b9c21"
down_revision = "edc745f354f5"
branch_labels = None
depends_on = None


def _slugify(value: str) -> str:
    text = (value or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-") or "categoria"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    current_columns = {
        column["name"] for column in inspector.get_columns("furniture_types")
    }

    if "name" in current_columns and "title" in current_columns:
        bind.execute(sa.text("""
                UPDATE furniture_types
                SET title = name
                WHERE (title IS NULL OR title = '')
                  AND name IS NOT NULL
                  AND name <> ''
                """))
        with op.batch_alter_table("furniture_types", schema=None) as batch_op:
            batch_op.drop_column("name")
    elif "name" in current_columns and "title" not in current_columns:
        with op.batch_alter_table("furniture_types", schema=None) as batch_op:
            batch_op.alter_column(
                "name",
                existing_type=sa.String(length=100),
                nullable=False,
                new_column_name="title",
            )

    current_columns = {
        column["name"] for column in inspector.get_columns("furniture_types")
    }
    if "description" in current_columns:
        with op.batch_alter_table("furniture_types", schema=None) as batch_op:
            batch_op.drop_column("description")

    bind.execute(sa.text("""
            UPDATE furniture_types
            SET title = CONCAT('categoria-', id)
            WHERE title IS NULL OR title = ''
            """))

    with op.batch_alter_table("furniture_types", schema=None) as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.String(length=100),
            nullable=False,
        )

    inspector = sa.inspect(bind)
    unique_constraints = inspector.get_unique_constraints("furniture_types")
    title_is_unique = any(
        set(constraint.get("column_names") or []) == {"title"}
        for constraint in unique_constraints
    )
    if not title_is_unique:
        op.create_unique_constraint(
            "uq_furniture_types_title", "furniture_types", ["title"]
        )

    rows = bind.execute(
        sa.text("SELECT id, title, slug FROM furniture_types ORDER BY id")
    ).fetchall()

    used: set[str] = set()
    for row in rows:
        if row.slug and row.slug.strip():
            used.add(row.slug)

    for row in rows:
        if row.slug and row.slug.strip():
            continue

        base_slug = _slugify(row.title)
        slug = base_slug
        counter = 2
        while slug in used:
            slug = f"{base_slug}-{counter}"
            counter += 1

        used.add(slug)
        bind.execute(
            sa.text("UPDATE furniture_types SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": row.id},
        )


def downgrade() -> None:
    with op.batch_alter_table("furniture_types", schema=None) as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    unique_constraints = inspector.get_unique_constraints("furniture_types")
    title_unique_name = None
    for constraint in unique_constraints:
        if set(constraint.get("column_names") or []) == {"title"}:
            title_unique_name = constraint.get("name")
            break
    if title_unique_name:
        op.drop_constraint(title_unique_name, "furniture_types", type_="unique")

    with op.batch_alter_table("furniture_types", schema=None) as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.String(length=100),
            nullable=False,
            new_column_name="name",
        )
