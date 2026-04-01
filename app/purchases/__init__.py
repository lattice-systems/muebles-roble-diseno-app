"""
Blueprint de Compras (Purchases).
"""

from flask import Blueprint

purchases_bp = Blueprint("purchases", __name__)

from . import routes  # noqa: F401, E402
