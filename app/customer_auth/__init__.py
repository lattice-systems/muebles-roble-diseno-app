"""Autenticación y cuenta de cliente para ecommerce."""

from flask import Blueprint

customer_auth_bp = Blueprint("customer_auth", __name__)

from . import routes  # noqa: E402, F401
