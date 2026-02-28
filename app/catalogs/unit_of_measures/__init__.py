"""
Módulo de gestión de unidades de medida.

Proporciona endpoints para CRUD de unidades de medida del catálogo.
"""

from flask import Blueprint

unit_of_measures_bp = Blueprint('unit_of_measures', __name__)

from . import routes  # noqa: E402, F401
