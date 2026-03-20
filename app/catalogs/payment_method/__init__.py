"""
Módulo de gestión de métodos de pago.

Proporciona endpoints para CRUD de métodos de pago del catálogo.
"""

from flask import Blueprint

payment_method_bp = Blueprint("payment_method", __name__)

from . import routes  # noqa: E402, F401