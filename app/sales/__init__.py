"""
Módulo de ventas POS.

Proporciona endpoints para la gestión de ventas físicas en tienda.
"""

from flask import Blueprint

sales_bp = Blueprint("sales", __name__)

from . import routes  # noqa: E402, F401
