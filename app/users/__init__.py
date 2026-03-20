"""
Módulo de gestión de usuarios.

Proporciona endpoints para CRUD de usuarios.
"""

from flask import Blueprint

users_bp = Blueprint("users", __name__)

from . import routes  # noqa: E402, F401
