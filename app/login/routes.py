"""
Rutas/Endpoints para el módulo de login.
"""

from flask import flash, redirect
from flask_security import auth_required, url_for_security
from flask_security.utils import logout_user

from app.login import login_bp


@login_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for_security("login"))


@login_bp.route("/logout", methods=["POST"])
@auth_required()
def logout():
    logout_user()
    flash("Has cerrado sesion correctamente.", "success")
    return redirect(url_for_security("login"))
