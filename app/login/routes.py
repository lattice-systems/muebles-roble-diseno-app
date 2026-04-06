"""
Rutas/Endpoints para el módulo de login.
"""

from flask import current_app, make_response, redirect, session
from flask_security import auth_required, url_for_security
from flask_security.utils import logout_user

from app.login import login_bp


def _expire_cookie(response, cookie_name: str, path: str | None, domain: str | None):
    response.delete_cookie(cookie_name, path=path or "/", domain=domain)


def _build_logout_response():
    response = make_response(redirect(url_for_security("login")))

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0, private"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'

    _expire_cookie(
        response,
        cookie_name=current_app.config.get("SESSION_COOKIE_NAME", "session"),
        path=current_app.config.get("SESSION_COOKIE_PATH", "/"),
        domain=current_app.config.get("SESSION_COOKIE_DOMAIN"),
    )
    _expire_cookie(
        response,
        cookie_name=current_app.config.get("REMEMBER_COOKIE_NAME", "remember_token"),
        path=current_app.config.get("REMEMBER_COOKIE_PATH", "/"),
        domain=current_app.config.get("REMEMBER_COOKIE_DOMAIN"),
    )

    return response


@login_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for_security("login"))


@login_bp.route("/logout", methods=["POST"])
@auth_required()
def logout():
    logout_user()
    session.clear()
    session.modified = True

    return _build_logout_response()
