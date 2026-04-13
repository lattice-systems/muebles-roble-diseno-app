"""Módulo de seguimiento de solicitudes de contacto/cita para muebles personalizados."""

from flask import Blueprint

contact_requests_bp = Blueprint("contact_requests", __name__)

from . import routes  # noqa: E402, F401
