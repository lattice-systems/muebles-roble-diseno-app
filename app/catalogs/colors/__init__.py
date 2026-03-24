"""
Módulo de gestión de colores.

Proporciona endpoints para CRUD de colores del catálogo.
"""

from flask import Blueprint

colors_bp = Blueprint("colors", __name__)

from . import routes  # noqa: E402, F401
