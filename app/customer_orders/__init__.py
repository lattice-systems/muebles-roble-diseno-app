"""
Módulo de Órdenes de Cliente (HU-14).

Permite registrar, gestionar y dar seguimiento a órdenes de clientes
utilizando productos existentes del catálogo.
"""

from flask import Blueprint

customer_orders_bp = Blueprint("customer_orders", __name__)

from . import routes  # noqa: E402, F401
