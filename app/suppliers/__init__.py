"""
Módulo de gestión de proveedores.

Proporciona endpoints para CRUD de proveedores.
"""

from flask import Blueprint

suppliers_bp = Blueprint("suppliers", __name__)

from . import routes  # noqa: E402, F401
