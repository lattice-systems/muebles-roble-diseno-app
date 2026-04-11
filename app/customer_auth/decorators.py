from __future__ import annotations

from functools import wraps

from flask import redirect, request, session, url_for

from app.extensions import db
from app.models.customer_user import CustomerUser

SESSION_KEY = "ecommerce_customer_user_id"
PENDING_2FA_USER_KEY = "ecommerce_customer_pending_2fa_user_id"
PENDING_2FA_NEXT_KEY = "ecommerce_customer_pending_2fa_next"
PENDING_2FA_SETUP_SECRET_KEY = "ecommerce_customer_pending_setup_secret"


def get_current_customer_user() -> CustomerUser | None:
    """Retorna el cliente autenticado para ecommerce basado en sesión."""
    raw_user_id = session.get(SESSION_KEY)
    if not raw_user_id:
        return None

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        session.pop(SESSION_KEY, None)
        session.modified = True
        return None

    customer_user = db.session.get(CustomerUser, user_id)
    if not customer_user or not customer_user.status:
        session.pop(SESSION_KEY, None)
        session.modified = True
        return None

    return customer_user


def login_customer_user(user_id: int) -> None:
    """Establece sesión de cliente autenticado."""
    session[SESSION_KEY] = int(user_id)
    clear_pending_2fa()
    session.modified = True


def logout_customer_user() -> None:
    """Elimina únicamente estado de sesión del cliente ecommerce."""
    session.pop(SESSION_KEY, None)
    clear_pending_2fa()
    session.pop(PENDING_2FA_SETUP_SECRET_KEY, None)
    session.modified = True


def set_pending_2fa(user_id: int, next_url: str | None = None) -> None:
    session[PENDING_2FA_USER_KEY] = int(user_id)
    if next_url:
        session[PENDING_2FA_NEXT_KEY] = next_url
    else:
        session.pop(PENDING_2FA_NEXT_KEY, None)
    session.modified = True


def get_pending_2fa_user() -> CustomerUser | None:
    raw_user_id = session.get(PENDING_2FA_USER_KEY)
    if not raw_user_id:
        return None

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        clear_pending_2fa()
        return None

    customer_user = db.session.get(CustomerUser, user_id)
    if not customer_user or not customer_user.status:
        clear_pending_2fa()
        return None

    return customer_user


def pop_pending_2fa_next() -> str | None:
    next_url = session.pop(PENDING_2FA_NEXT_KEY, None)
    session.modified = True
    return next_url


def clear_pending_2fa() -> None:
    session.pop(PENDING_2FA_USER_KEY, None)
    session.pop(PENDING_2FA_NEXT_KEY, None)


def customer_auth_required(view_func):
    """Requiere autenticación de cliente ecommerce."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not get_current_customer_user():
            return redirect(url_for("customer_auth.login", next=request.url))
        return view_func(*args, **kwargs)

    return wrapper
