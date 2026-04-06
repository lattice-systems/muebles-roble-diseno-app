"""Rutas del modulo de auditoria de seguridad."""

from __future__ import annotations

from flask import render_template, request
from flask_security import auth_required

from app.security_audit import security_audit_bp
from app.security_audit.services import SecurityAuditService


@security_audit_bp.route("/", methods=["GET"])
@auth_required()
def index():
    """Lista paginada de eventos de seguridad con filtros."""
    search_term = request.args.get("q", "").strip()
    event_type = request.args.get("event_type", "").strip()
    result = request.args.get("result", "").strip()
    date_from_raw = request.args.get("date_from", "").strip()
    date_to_raw = request.args.get("date_to", "").strip()
    page = request.args.get("page", 1, type=int)

    date_from = SecurityAuditService.parse_date(date_from_raw)
    date_to = SecurityAuditService.parse_date(date_to_raw)

    pagination = SecurityAuditService.get_logs(
        event_type=event_type or None,
        result=result or None,
        search_term=search_term or None,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=20,
    )

    options = SecurityAuditService.get_filter_options()

    return render_template(
        "admin/security_audit/index.html",
        logs=pagination.items,
        pagination=pagination,
        search_term=search_term,
        event_type=event_type,
        result=result,
        date_from=date_from_raw,
        date_to=date_to_raw,
        event_type_options=options["event_types"],
        result_options=options["results"],
    )
