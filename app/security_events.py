"""Registro de eventos de seguridad basado en señales de autenticacion."""

from __future__ import annotations

from typing import Any

from flask import current_app, has_request_context, request
from flask_login import user_logged_out
from flask_security.signals import (
    password_changed,
    password_reset,
    user_authenticated,
    user_unauthenticated,
)

from app.extensions import db
from app.shared.security_logging import log_security_event


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


def register_security_event_handlers(app) -> None:
    """Conecta listeners de seguridad al ciclo de vida de la app."""
    user_authenticated.connect(_on_user_authenticated, sender=app, weak=False)
    user_logged_out.connect(_on_user_logged_out, sender=app, weak=False)
    password_changed.connect(_on_password_changed, sender=app, weak=False)
    password_reset.connect(_on_password_reset, sender=app, weak=False)
    user_unauthenticated.connect(_on_user_unauthenticated, sender=app, weak=False)
