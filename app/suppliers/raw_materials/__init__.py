"""
Modulo de gestión de materias primas.

Proporciona endpoints para CRUD de materias primas.
"""

from flask import Blueprint
raw_materials_bp = Blueprint("raw_materials", __name__)
from . import routes  # noqa: E402, F401
