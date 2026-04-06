"""Utilidades para registro de auditoria desde capa de aplicacion."""

from __future__ import annotations

from typing import Any

from flask import current_app, has_app_context
from flask_login import current_user

from app.extensions import db
from app.models.audit_log import AuditLog


def _get_dialect_name() -> str | None:
    """Retorna el dialecto activo de SQLAlchemy (mysql, sqlite, etc.)."""
    try:
        bind = db.session.get_bind()
        if not bind:
            return None
        return getattr(bind.dialect, "name", None)
    except Exception:
        return None


def resolve_current_user_id() -> int | None:
    """Obtiene el id de usuario autenticado cuando existe contexto de login."""
    if not getattr(current_user, "is_authenticated", False):
        return None

    raw_user_id = getattr(current_user, "id", None)
    if raw_user_id is None:
        return None

    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return None


def should_write_application_audit() -> bool:
    """Define si se debe insertar auditoria manual desde la aplicacion.

    Politica por defecto:
    - MySQL: NO (se evita duplicado porque escribe el trigger).
    - Otros dialectos (ej. SQLite tests): SI.

    Overrides opcionales por config:
    - AUDIT_FORCE_APPLICATION_LOGS (bool)
    - AUDIT_ENABLE_APPLICATION_FALLBACK (bool, default True)
    """
    if not has_app_context():
        return True

    force = current_app.config.get("AUDIT_FORCE_APPLICATION_LOGS")
    if force is not None:
        return bool(force)

    enabled = bool(current_app.config.get("AUDIT_ENABLE_APPLICATION_FALLBACK", True))
    if not enabled:
        return False

    return _get_dialect_name() != "mysql"


def _resolve_record_id(
    *,
    explicit_record_id: str | int | None,
    previous_data: dict[str, Any] | None,
    new_data: dict[str, Any] | None,
) -> str | None:
    if explicit_record_id is not None:
        return str(explicit_record_id)

    for payload in (new_data, previous_data):
        if isinstance(payload, dict) and payload.get("id") is not None:
            return str(payload.get("id"))

    return None


def log_application_audit(
    *,
    table_name: str,
    action: str,
    previous_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
    user_id: int | None = None,
    record_id: str | int | None = None,
) -> None:
    """Inserta auditoria desde aplicacion si la politica actual lo permite."""
    if not should_write_application_audit():
        return

    actor_id = user_id if user_id is not None else resolve_current_user_id()

    entry = AuditLog(
        table_name=table_name,
        action=(action or "").upper(),
        user_id=actor_id,
        previous_data=previous_data,
        new_data=new_data,
        record_id=_resolve_record_id(
            explicit_record_id=record_id,
            previous_data=previous_data,
            new_data=new_data,
        ),
        source="application",
    )
    db.session.add(entry)
