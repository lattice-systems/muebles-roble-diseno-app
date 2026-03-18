"""
Rutas/Endpoints para el módulo de login.
"""

from flask import redirect
from flask_security import url_for_security

from app.login import login_bp


@login_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for_security("login"))
