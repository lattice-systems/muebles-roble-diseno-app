"""Registro de eventos de seguridad basado en señales de autenticacion."""

from __future__ import annotations

from typing import Any

from flask import current_app, has_request_context, request, session
from flask_login import current_user
from flask_login import user_logged_out
from flask_security.signals import (
    password_changed,
    password_reset,
    user_authenticated,
    user_unauthenticated,
)

from app.extensions import db
from app.shared.security_logging import log_security_event

LOGIN_ATTEMPTS_SESSION_KEY = "security_login_attempts"


def _request_ip() -> str | None:
    if not has_request_context():
        return None
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def _request_user_agent() -> str | None:
    if not has_request_context():
        return None
    return request.headers.get("User-Agent")


def _request_path() -> str | None:
    if not has_request_context():
        return None
    return request.path


def _request_identifier() -> str | None:
    if not has_request_context():
        return None

    json_data = request.get_json(silent=True) or {}
    return (
        request.form.get("email")
        or request.form.get("username")
        or json_data.get("email")
        or json_data.get("username")
    )


def _is_security_login_request() -> bool:
    if not has_request_context() or request.method.upper() != "POST":
        return False

    endpoint = (request.endpoint or "").strip()
    if endpoint == "security.login":
        return True

    path = (request.path or "").strip().rstrip("/")
    return path == "/login"


def _safe_commit_log(**payload: Any) -> None:
    try:
        log_security_event(commit=True, **payload)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("No se pudo registrar evento de seguridad: %s", exc)


def _on_user_authenticated(sender, user=None, authn_via=None, **extra):
    auth_methods = list(authn_via or [])
    _safe_commit_log(
        event_type="auth.login.success",
        result="success",
        user_id=getattr(user, "id", None),
        email_or_identifier=getattr(user, "email", None),
        ip_address=_request_ip(),
        user_agent=_request_user_agent(),
        context_data={"authn_via": auth_methods, "path": _request_path()},
        source="security_signal",
    )
    if has_request_context():
        session.pop(LOGIN_ATTEMPTS_SESSION_KEY, None)


def _on_user_logged_out(sender, user=None, **extra):
    _safe_commit_log(
        event_type="auth.logout",
        result="success",
        user_id=getattr(user, "id", None),
        email_or_identifier=getattr(user, "email", None),
        ip_address=_request_ip(),
        user_agent=_request_user_agent(),
        context_data={"path": _request_path()},
        source="security_signal",
    )


def _on_password_changed(sender, user=None, **extra):
    _safe_commit_log(
        event_type="auth.password.changed",
        result="success",
        user_id=getattr(user, "id", None),
        email_or_identifier=getattr(user, "email", None),
        ip_address=_request_ip(),
        user_agent=_request_user_agent(),
        context_data={"path": _request_path()},
        source="security_signal",
    )


def _on_password_reset(sender, user=None, **extra):
    _safe_commit_log(
        event_type="auth.password.reset.completed",
        result="success",
        user_id=getattr(user, "id", None),
        email_or_identifier=getattr(user, "email", None),
        ip_address=_request_ip(),
        user_agent=_request_user_agent(),
        context_data={"path": _request_path()},
        source="security_signal",
    )


def _on_user_unauthenticated(sender, **extra):
    _safe_commit_log(
        event_type="auth.unauthenticated.access",
        result="denied",
        user_id=None,
        email_or_identifier=None,
        ip_address=_request_ip(),
        user_agent=_request_user_agent(),
        reason="Ruta protegida sin autenticacion",
        context_data={"path": _request_path()},
        source="security_signal",
    )


def process_login_attempt_response(response):
    """Registra intentos de login fallidos y mantiene contador por sesion."""
    if not _is_security_login_request():
        return response

    if getattr(current_user, "is_authenticated", False):
        session.pop(LOGIN_ATTEMPTS_SESSION_KEY, None)
        return response

    attempts = int(session.get(LOGIN_ATTEMPTS_SESSION_KEY, 0)) + 1
    session[LOGIN_ATTEMPTS_SESSION_KEY] = attempts
    session.modified = True

    _safe_commit_log(
        event_type="auth.login.failed",
        result="denied",
        user_id=None,
        email_or_identifier=_request_identifier(),
        ip_address=_request_ip(),
        user_agent=_request_user_agent(),
        reason=f"Intento fallido #{attempts}",
        context_data={
            "path": _request_path(),
            "attempt": attempts,
            "status_code": getattr(response, "status_code", None),
        },
        source="security_signal",
    )
    return response


def register_security_event_handlers(app) -> None:
    """Conecta listeners de seguridad al ciclo de vida de la app."""
    user_authenticated.connect(_on_user_authenticated, sender=app, weak=False)
    user_logged_out.connect(_on_user_logged_out, sender=app, weak=False)
    password_changed.connect(_on_password_changed, sender=app, weak=False)
    password_reset.connect(_on_password_reset, sender=app, weak=False)
    user_unauthenticated.connect(_on_user_unauthenticated, sender=app, weak=False)
