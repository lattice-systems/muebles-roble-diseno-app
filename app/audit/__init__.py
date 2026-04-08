"""Modulo de auditoria para consulta y trazabilidad de cambios."""

from flask import Blueprint

audit_bp = Blueprint("audit", __name__)

from . import routes  # noqa: E402,F401
