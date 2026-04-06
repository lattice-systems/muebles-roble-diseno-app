"""Pruebas para el registro de eventos de seguridad."""

from __future__ import annotations

from flask_login import user_logged_out
from flask_security.signals import password_changed, user_authenticated

from app.models.security_event_log import SecurityEventLog
from app.shared.security_logging import log_security_event


class TestSecurityEventLogging:
    """Valida helper y listeners de señales de seguridad."""

    def test_log_security_event_helper(self, app, db_session, seed_basic_data):
        user = seed_basic_data["user"]

        log_security_event(
            event_type="auth.custom",
            result="success",
            user_id=user.id,
            email_or_identifier=user.email,
            ip_address="127.0.0.1",
            user_agent="pytest",
            reason="manual test",
            context_data={"foo": "bar"},
            source="unit_test",
            commit=True,
        )

        row = SecurityEventLog.query.order_by(SecurityEventLog.id.desc()).first()
        assert row is not None
        assert row.event_type == "auth.custom"
        assert row.result == "success"
        assert row.user_id == user.id
        assert row.source == "unit_test"

    def test_security_signals_create_events(self, app, db_session, seed_basic_data):
        user = seed_basic_data["user"]

        with app.test_request_context("/login", headers={"User-Agent": "pytest-agent"}):
            user_authenticated.send(app, user=user, authn_via=["password"])

        with app.test_request_context(
            "/change", headers={"User-Agent": "pytest-agent"}
        ):
            password_changed.send(app, user=user)

        with app.test_request_context(
            "/logout", headers={"User-Agent": "pytest-agent"}
        ):
            user_logged_out.send(app, user=user)

        events = SecurityEventLog.query.order_by(SecurityEventLog.id.asc()).all()
        event_types = [item.event_type for item in events]

        assert "auth.login.success" in event_types
        assert "auth.password.changed" in event_types
        assert "auth.logout" in event_types
