"""
Módulo de gestión de roles.

Proporciona endpoints para CRUD de roles del catálogo.
"""

from flask import Blueprint

roles_bp = Blueprint("roles", __name__)

from . import routes  # noqa: E402, F401
