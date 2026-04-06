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
    per_page = request.args.get("per_page", 10, type=int)
    allowed_per_page = {10, 20, 50, 100}
    if per_page not in allowed_per_page:
        per_page = 10

    date_from = SecurityAuditService.parse_date(date_from_raw)
    date_to = SecurityAuditService.parse_date(date_to_raw)

    pagination = SecurityAuditService.get_logs(
        event_type=event_type or None,
        result=result or None,
        search_term=search_term or None,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )

    options = SecurityAuditService.get_filter_options()
    logs = [SecurityAuditService.to_list_item(entry) for entry in pagination.items]
    event_type_options = [
        (value, SecurityAuditService.event_label(value))
        for value in options["event_types"]
    ]
    result_options = [
        (value, SecurityAuditService.result_label(value))
        for value in options["results"]
    ]

    return render_template(
        "admin/security_audit/index.html",
        logs=logs,
        pagination=pagination,
        search_term=search_term,
        event_type=event_type,
        result=result,
        date_from=date_from_raw,
        date_to=date_to_raw,
        per_page=per_page,
        event_type_options=event_type_options,
        result_options=result_options,
    )
