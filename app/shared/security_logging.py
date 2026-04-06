"""Utilidades para registro de eventos de seguridad."""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models.security_event_log import SecurityEventLog


def log_security_event(
    *,
    event_type: str,
    result: str = "info",
    user_id: int | None = None,
    email_or_identifier: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    reason: str | None = None,
    context_data: dict[str, Any] | None = None,
    source: str = "application",
    commit: bool = False,
) -> SecurityEventLog:
    """Crea y persiste un evento de seguridad en `security_event_log`."""
    entry = SecurityEventLog(
        event_type=(event_type or "").strip(),
        result=(result or "info").strip().lower(),
        user_id=user_id,
        email_or_identifier=email_or_identifier,
        ip_address=ip_address,
        user_agent=user_agent,
        reason=reason,
        context_data=context_data,
        source=source,
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry
