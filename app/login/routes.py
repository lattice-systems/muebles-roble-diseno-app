"""
Rutas/Endpoints para el módulo de login.
"""

from flask import render_template

from app.login import login_bp


@login_bp.route("/", methods=["GET"])
def index():
    return render_template("login/index.html")
