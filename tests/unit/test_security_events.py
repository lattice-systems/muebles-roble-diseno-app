"""Pruebas para el registro de eventos de seguridad."""

from __future__ import annotations

import time

from flask import session
from flask_login import user_logged_out
from flask_security.signals import password_changed, user_authenticated

from app.models.security_event_log import SecurityEventLog
from app.security_events import (
    LOGIN_BLOCKED_UNTIL_SESSION_KEY,
    LOGIN_ATTEMPTS_SESSION_KEY,
    enforce_login_attempt_limit,
    process_login_attempt_response,
)
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

    def test_failed_login_attempts_are_logged(self, app, db_session):
        with app.test_request_context(
            "/login", method="POST", data={"email": "fail@test.com"}
        ):
            response = app.response_class(status=200)
            process_login_attempt_response(response)
            process_login_attempt_response(response)

            assert int(session["security_login_attempts"]) == 2

        events = SecurityEventLog.query.filter_by(event_type="auth.login.failed").all()
        assert len(events) == 2
        assert events[0].email_or_identifier == "fail@test.com"
        assert events[0].context_data.get("attempt") == 1
        assert events[1].context_data.get("attempt") == 2

    def test_login_is_locked_after_three_attempts(self, app, db_session):
        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": "locked@test.com"},
            headers={"Accept": "application/json"},
        ):
            session[LOGIN_ATTEMPTS_SESSION_KEY] = 3
            response = enforce_login_attempt_limit()

            assert response is not None
            assert response.status_code == 429
            assert response.json["error"]["code"] == 429
            assert response.json["meta"]["retry_after_seconds"] > 0
            assert int(session[LOGIN_ATTEMPTS_SESSION_KEY]) == 3
            assert int(session[LOGIN_BLOCKED_UNTIL_SESSION_KEY]) > int(time.time())

        lock_event = SecurityEventLog.query.filter_by(
            event_type="auth.account.locked"
        ).first()
        assert lock_event is not None
        assert lock_event.email_or_identifier == "locked@test.com"
        assert lock_event.context_data.get("max_attempts") == 3

    def test_blocked_login_does_not_increment_failed_attempt_counter(
        self, app, db_session
    ):
        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": "blocked@test.com"},
            headers={"Accept": "application/json"},
        ):
            session[LOGIN_ATTEMPTS_SESSION_KEY] = 3
            session[LOGIN_BLOCKED_UNTIL_SESSION_KEY] = int(time.time()) + 300
            enforce_login_attempt_limit()

            response = app.response_class(status=429)
            process_login_attempt_response(response)

            assert int(session[LOGIN_ATTEMPTS_SESSION_KEY]) == 3

        failed_events = SecurityEventLog.query.filter_by(
            event_type="auth.login.failed"
        ).all()
        assert len(failed_events) == 0

    def test_lock_expires_and_auto_unlock_is_logged(self, app, db_session):
        with app.test_request_context(
            "/login",
            method="POST",
            data={"email": "unlock@test.com"},
            headers={"Accept": "application/json"},
        ):
            session[LOGIN_ATTEMPTS_SESSION_KEY] = 3
            session[LOGIN_BLOCKED_UNTIL_SESSION_KEY] = int(time.time()) - 10

            response = enforce_login_attempt_limit()
            assert response is None
            assert LOGIN_ATTEMPTS_SESSION_KEY not in session
            assert LOGIN_BLOCKED_UNTIL_SESSION_KEY not in session

        unlock_event = SecurityEventLog.query.filter_by(
            event_type="auth.account.unlocked.auto"
        ).first()
        assert unlock_event is not None
        assert unlock_event.email_or_identifier == "unlock@test.com"
