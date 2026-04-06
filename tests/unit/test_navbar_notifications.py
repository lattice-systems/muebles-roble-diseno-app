"""Pruebas para las notificaciones del navbar administrativo."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.models.audit_log import AuditLog
from app.models.navbar_notification_dismissal import NavbarNotificationDismissal
from app.models.security_event_log import SecurityEventLog
from app.shared import navbar_notifications


class DummyAuthenticatedUser:
    def __init__(self, user_id: int | None = None):
        self.is_authenticated = True
        self.id = user_id


def test_navbar_notifications_merge_security_and_audit_events(
    app, db_session, seed_basic_data, monkeypatch
):
    user = seed_basic_data["user"]
    now = datetime.utcnow()

    db_session.add(
        SecurityEventLog(
            event_type="auth.account.locked",
            result="denied",
            user_id=user.id,
            email_or_identifier=user.email,
            ip_address="127.0.0.1",
            reason="Tres intentos fallidos",
            source="unit_test",
            timestamp=now,
        )
    )
    db_session.add(
        AuditLog(
            table_name="users",
            action="DELETE",
            user_id=user.id,
            record_id="99",
            source="unit_test",
            timestamp=now - timedelta(minutes=5),
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        navbar_notifications, "current_user", DummyAuthenticatedUser(user.id)
    )

    with app.test_request_context("/admin"):
        data = navbar_notifications.build_navbar_notifications()

    assert data["count"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["kind"] == "security"
    assert data["items"][0]["title"] == "Cuenta bloqueada por intentos"
    assert data["items"][0]["href"].endswith("/details")
    assert data["items"][1]["kind"] == "audit"
    assert data["items"][1]["href"].endswith("/details")


def test_navbar_notifications_returns_empty_for_anonymous_user(monkeypatch):
    class AnonymousUser:
        is_authenticated = False

    monkeypatch.setattr(navbar_notifications, "current_user", AnonymousUser())

    data = navbar_notifications.build_navbar_notifications()

    assert data == {"items": [], "count": 0}


def test_navbar_notifications_can_be_dismissed(
    app, db_session, seed_basic_data, monkeypatch
):
    user = seed_basic_data["user"]
    now = datetime.utcnow()

    security_event = SecurityEventLog(
        event_type="auth.account.locked",
        result="denied",
        user_id=user.id,
        email_or_identifier=user.email,
        ip_address="127.0.0.1",
        reason="Tres intentos fallidos",
        source="unit_test",
        timestamp=now,
    )
    audit_event = AuditLog(
        table_name="users",
        action="DELETE",
        user_id=user.id,
        record_id="99",
        source="unit_test",
        timestamp=now - timedelta(minutes=5),
    )
    db_session.add(security_event)
    db_session.add(audit_event)
    db_session.commit()

    monkeypatch.setattr(
        navbar_notifications, "current_user", DummyAuthenticatedUser(user.id)
    )

    with app.test_request_context("/admin"):
        feed = navbar_notifications.build_navbar_notifications()
        assert feed["count"] == 2

        removed = navbar_notifications.dismiss_notification(
            "security", security_event.id
        )
        assert removed is True

        feed_after = navbar_notifications.build_navbar_notifications()

    assert feed_after["count"] == 1
    assert len(feed_after["items"]) == 1
    assert feed_after["items"][0]["source_kind"] == "audit"
    assert (
        NavbarNotificationDismissal.query.filter_by(
            user_id=user.id,
            source_kind="security",
            source_id=security_event.id,
        ).first()
        is not None
    )
