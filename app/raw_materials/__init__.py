"""
Módulo de gestión de materias primas.
"""

from flask import Blueprint

raw_materials_bp = Blueprint("raw_materials", __name__)

from . import routes  # noqa: F401, E402
