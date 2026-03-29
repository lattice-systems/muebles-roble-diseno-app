"""Módulo de e-commerce."""

from flask import Blueprint

ecommerce_bp = Blueprint("ecommerce", __name__)

from . import routes  # noqa: E402, F401
