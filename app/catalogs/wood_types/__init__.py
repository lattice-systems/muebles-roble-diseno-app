"""
Módulo de gestión de tipos de madera.

Proporciona endpoints para CRUD de tipos de madera del catálogo.
"""

from flask import Blueprint

woods_types_bp = Blueprint('woods_types', __name__)

from . import routes  # noqa: E402, F401
