"""Alertas resumidas para la campana del navbar administrativo."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from flask import url_for
from flask_login import current_user
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.audit.services import AuditService
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.navbar_notification_dismissal import NavbarNotificationDismissal
from app.models.security_event_log import SecurityEventLog
from app.security_audit.services import SecurityAuditService

IMPORTANT_SECURITY_EVENTS = {
    "auth.login.failed",
    "auth.account.locked",
    "auth.unauthenticated.access",
    "auth.rbac.denied",
}

IMPORTANT_SECURITY_RESULTS = {"denied", "error"}
IMPORTANT_AUDIT_ACTIONS = {"DELETE"}
DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_LIMIT = 5
_DISMISSAL_TABLE_NAME = "navbar_notification_dismissals"


def _safe_timestamp(value: datetime | None) -> datetime:
    return value or datetime.min


def _format_security_notification(entry: SecurityEventLog) -> dict:
    event_label = SecurityAuditService.event_label(entry.event_type)
    actor = entry.email_or_identifier or "Sistema"
    message = actor
    if entry.reason:
        message = f"{actor} · {entry.reason}"

    return {
        "kind": "security",
        "title": event_label,
        "message": message,
        "href": url_for("security_audit.index", event_type=entry.event_type),
        "timestamp": entry.timestamp,
        "severity": (
            "danger"
            if entry.event_type in {"auth.account.locked", "auth.rbac.denied"}
            else "warning"
        ),
        "source": entry.source,
        "source_kind": "security",
        "source_id": entry.id,
        "dismiss_url": url_for(
            "notifications.dismiss",
            source_kind="security",
            source_id=entry.id,
        ),
    }


def _format_audit_notification(entry: AuditLog) -> dict:
    action_label = AuditService.get_action_label(entry.action)
    record_label = entry.record_id or "sin identificador"
    message = f"{entry.table_name} #{record_label}"

    return {
        "kind": "audit",
        "title": f"{action_label} importante",
        "message": message,
        "href": url_for(
            "audit.index",
            action=entry.action,
            table_name=entry.table_name,
        ),
        "timestamp": entry.timestamp,
        "severity": "danger",
        "source": entry.source,
        "source_kind": "audit",
        "source_id": entry.id,
        "dismiss_url": url_for(
            "notifications.dismiss",
            source_kind="audit",
            source_id=entry.id,
        ),
    }


def _build_important_security_notifications(cutoff: datetime) -> list[dict]:
    query = (
        SecurityEventLog.query.filter(SecurityEventLog.timestamp >= cutoff)
        .filter(
            SecurityEventLog.event_type.in_(IMPORTANT_SECURITY_EVENTS)
            | SecurityEventLog.result.in_(IMPORTANT_SECURITY_RESULTS)
        )
        .order_by(SecurityEventLog.timestamp.desc(), SecurityEventLog.id.desc())
    )
    return [_format_security_notification(entry) for entry in query.limit(10).all()]


def _build_important_audit_notifications(cutoff: datetime) -> list[dict]:
    query = (
        AuditLog.query.filter(AuditLog.timestamp >= cutoff)
        .filter(AuditLog.action.in_(IMPORTANT_AUDIT_ACTIONS))
        .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
    )
    return [_format_audit_notification(entry) for entry in query.limit(10).all()]


def _sort_notifications(items: Iterable[dict]) -> list[dict]:
    return sorted(
        items, key=lambda item: _safe_timestamp(item.get("timestamp")), reverse=True
    )


def _dismissal_table_exists() -> bool:
    try:
        return inspect(db.engine).has_table(_DISMISSAL_TABLE_NAME)
    except SQLAlchemyError:
        return False


def _dismissed_notification_keys() -> set[tuple[str, int]]:
    if not getattr(current_user, "is_authenticated", False):
        return set()

    user_id = getattr(current_user, "id", None)
    if user_id is None:
        return set()

    if not _dismissal_table_exists():
        return set()

    dismissed_rows = (
        NavbarNotificationDismissal.query.with_entities(
            NavbarNotificationDismissal.source_kind,
            NavbarNotificationDismissal.source_id,
        )
        .filter(NavbarNotificationDismissal.user_id == user_id)
        .all()
    )
    return {
        (row[0], int(row[1])) for row in dismissed_rows if row[0] and row[1] is not None
    }


def dismiss_notification(source_kind: str, source_id: int) -> bool:
    if not getattr(current_user, "is_authenticated", False):
        return False

    user_id = getattr(current_user, "id", None)
    if user_id is None:
        return False

    if not _dismissal_table_exists():
        return False

    normalized_kind = (source_kind or "").strip().lower()
    normalized_id = int(source_id)

    existing = NavbarNotificationDismissal.query.filter_by(
        user_id=user_id,
        source_kind=normalized_kind,
        source_id=normalized_id,
    ).first()
    if existing:
        return False

    db.session.add(
        NavbarNotificationDismissal(
            user_id=user_id,
            source_kind=normalized_kind,
            source_id=normalized_id,
        )
    )
    db.session.commit()
    return True


def dismiss_notifications(items: Iterable[dict]) -> int:
    if not getattr(current_user, "is_authenticated", False):
        return 0

    user_id = getattr(current_user, "id", None)
    if user_id is None:
        return 0

    if not _dismissal_table_exists():
        return 0

    new_rows: list[NavbarNotificationDismissal] = []
    dismissed_keys = _dismissed_notification_keys()

    for item in items:
        source_kind = item.get("source_kind")
        source_id = item.get("source_id")
        if not source_kind or source_id is None:
            continue

        key = (str(source_kind), int(source_id))
        if key in dismissed_keys:
            continue

        new_rows.append(
            NavbarNotificationDismissal(
                user_id=user_id,
                source_kind=str(source_kind),
                source_id=int(source_id),
            )
        )
        dismissed_keys.add(key)

    if not new_rows:
        return 0

    db.session.add_all(new_rows)
    db.session.commit()
    return len(new_rows)


def build_navbar_notifications(
    *,
    limit: int = DEFAULT_LIMIT,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
    include_dismissed: bool = False,
) -> dict[str, object]:
    """Construye las alertas que se muestran en la campana del navbar."""
    if not getattr(current_user, "is_authenticated", False):
        return {"items": [], "count": 0}

    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
    security_notifications = _build_important_security_notifications(cutoff)
    audit_notifications = _build_important_audit_notifications(cutoff)
    notifications = _sort_notifications([*security_notifications, *audit_notifications])

    if not include_dismissed:
        dismissed_keys = _dismissed_notification_keys()
        notifications = [
            item
            for item in notifications
            if (item["source_kind"], int(item["source_id"])) not in dismissed_keys
        ]

    limited_notifications = notifications[:limit]

    return {"items": limited_notifications, "count": len(notifications)}
