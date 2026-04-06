"""Registro de eventos de seguridad basado en señales de autenticacion."""

from __future__ import annotations

import time
from typing import Any

from flask import current_app, g, has_request_context, jsonify, request, session
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
LOGIN_BLOCKED_UNTIL_SESSION_KEY = "security_login_blocked_until"
DEFAULT_MAX_LOGIN_ATTEMPTS = 3
DEFAULT_LOGIN_LOCK_MINUTES = 15


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


def _max_login_attempts() -> int:
    if not has_request_context():
        return DEFAULT_MAX_LOGIN_ATTEMPTS

    configured = current_app.config.get(
        "SECURITY_MAX_LOGIN_ATTEMPTS", DEFAULT_MAX_LOGIN_ATTEMPTS
    )
    try:
        value = int(configured)
    except (TypeError, ValueError):
        return DEFAULT_MAX_LOGIN_ATTEMPTS
    return max(1, value)


def _lock_minutes() -> int:
    if not has_request_context():
        return DEFAULT_LOGIN_LOCK_MINUTES

    configured = current_app.config.get(
        "SECURITY_LOGIN_LOCK_MINUTES", DEFAULT_LOGIN_LOCK_MINUTES
    )
    try:
        value = int(configured)
    except (TypeError, ValueError):
        return DEFAULT_LOGIN_LOCK_MINUTES
    return max(1, value)


def _get_blocked_until_epoch() -> int | None:
    raw_value = session.get(LOGIN_BLOCKED_UNTIL_SESSION_KEY)
    if raw_value is None:
        return None

    try:
        return int(raw_value)
    except (TypeError, ValueError):
        session.pop(LOGIN_BLOCKED_UNTIL_SESSION_KEY, None)
        return None


def _clear_lock_state(reset_attempts: bool = False) -> None:
    session.pop(LOGIN_BLOCKED_UNTIL_SESSION_KEY, None)
    if reset_attempts:
        session.pop(LOGIN_ATTEMPTS_SESSION_KEY, None)


def _set_lock_window() -> int:
    lock_until = int(time.time()) + (_lock_minutes() * 60)
    session[LOGIN_BLOCKED_UNTIL_SESSION_KEY] = lock_until
    session.modified = True
    return lock_until


def _wants_json_response() -> bool:
    if request.is_json:
        return True

    best = request.accept_mimetypes.best
    if best == "application/json":
        return True

    if (
        request.accept_mimetypes.accept_json
        and not request.accept_mimetypes.accept_html
    ):
        return True

    return False


def _build_locked_response(locked_until_epoch: int):
    retry_after_seconds = max(1, locked_until_epoch - int(time.time()))

    if _wants_json_response():
        payload = {
            "success": False,
            "error": {
                "code": 429,
                "message": "Demasiados intentos de inicio de sesion. Intenta mas tarde.",
            },
            "meta": {
                "retry_after_seconds": retry_after_seconds,
            },
        }
        response = jsonify(payload)
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after_seconds)
        return response

    response = current_app.response_class(
        response="Demasiados intentos de inicio de sesion. Intenta mas tarde.",
        status=429,
        mimetype="text/plain",
    )
    response.headers["Retry-After"] = str(retry_after_seconds)
    return response


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
        _clear_lock_state(reset_attempts=True)


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

    if getattr(g, "skip_login_attempt_tracking", False):
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


def enforce_login_attempt_limit():
    """Bloquea POST /login cuando se alcanza el maximo de intentos fallidos."""
    if not _is_security_login_request():
        return None

    if getattr(current_user, "is_authenticated", False):
        return None

    attempts = int(session.get(LOGIN_ATTEMPTS_SESSION_KEY, 0))
    max_attempts = _max_login_attempts()

    blocked_until_epoch = _get_blocked_until_epoch()
    now_epoch = int(time.time())

    if blocked_until_epoch and blocked_until_epoch <= now_epoch:
        _clear_lock_state(reset_attempts=True)
        _safe_commit_log(
            event_type="auth.account.unlocked.auto",
            result="success",
            user_id=None,
            email_or_identifier=_request_identifier(),
            ip_address=_request_ip(),
            user_agent=_request_user_agent(),
            reason="Desbloqueo automatico por expiracion de ventana de bloqueo",
            context_data={
                "path": _request_path(),
                "max_attempts": max_attempts,
                "lock_minutes": _lock_minutes(),
            },
            source="security_signal",
        )
        return None

    if not blocked_until_epoch and attempts < max_attempts:
        return None

    g.skip_login_attempt_tracking = True
    if not blocked_until_epoch:
        blocked_until_epoch = _set_lock_window()
        _safe_commit_log(
            event_type="auth.account.locked",
            result="denied",
            user_id=None,
            email_or_identifier=_request_identifier(),
            ip_address=_request_ip(),
            user_agent=_request_user_agent(),
            reason=(
                f"Cuenta bloqueada temporalmente por superar {max_attempts} intentos"
            ),
            context_data={
                "path": _request_path(),
                "attempt": attempts,
                "max_attempts": max_attempts,
                "lock_minutes": _lock_minutes(),
                "blocked_until_epoch": blocked_until_epoch,
            },
            source="security_signal",
        )

    return _build_locked_response(blocked_until_epoch)


def register_security_event_handlers(app) -> None:
    """Conecta listeners de seguridad al ciclo de vida de la app."""
    user_authenticated.connect(_on_user_authenticated, sender=app, weak=False)
    user_logged_out.connect(_on_user_logged_out, sender=app, weak=False)
    password_changed.connect(_on_password_changed, sender=app, weak=False)
    password_reset.connect(_on_password_reset, sender=app, weak=False)
    user_unauthenticated.connect(_on_user_unauthenticated, sender=app, weak=False)
