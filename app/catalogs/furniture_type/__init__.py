"""
Módulo de gestión de tipos de mueble.

Proporciona endpoints para CRUD de tipo de mueble del catálogo.
"""

from flask import Blueprint

furniture_type_bp = Blueprint('furniture_type', __name__)

from . import routes  # noqa: E402, F401
