"""Modulo de auditoria de seguridad para eventos de acceso."""

from flask import Blueprint

security_audit_bp = Blueprint("security_audit", __name__)

from . import routes  # noqa: E402,F401
