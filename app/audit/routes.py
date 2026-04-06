"""Rutas del modulo de auditoria."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_security import auth_required

from app.audit import audit_bp
from app.audit.services import AuditService
from app.exceptions import NotFoundError


@audit_bp.route("/", methods=["GET"])
@auth_required()
def index():
    """Lista paginada de eventos de auditoria con filtros."""
    search_term = request.args.get("q", "").strip()
    table_name = request.args.get("table", "").strip()
    action = request.args.get("action", "").strip()
    source = request.args.get("source", "").strip()
    user_id = request.args.get("user_id", type=int)
    date_from_raw = request.args.get("date_from", "").strip()
    date_to_raw = request.args.get("date_to", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    allowed_per_page = {10, 20, 50, 100}
    if per_page not in allowed_per_page:
        per_page = 10

    date_from = AuditService.parse_date(date_from_raw)
    date_to = AuditService.parse_date(date_to_raw)

    pagination = AuditService.get_logs(
        search_term=search_term or None,
        table_name=table_name or None,
        action=action or None,
        source=source or None,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )

    options = AuditService.get_filter_options()
    action_options = [
        (value, AuditService.get_action_label(value)) for value in options["actions"]
    ]
    source_options = [
        (value, AuditService.get_source_label(value)) for value in options["sources"]
    ]
    logs = [AuditService.to_list_item(entry) for entry in pagination.items]

    return render_template(
        "admin/audit/index.html",
        logs=logs,
        pagination=pagination,
        search_term=search_term,
        table_name=table_name,
        action=action,
        source=source,
        user_id=user_id,
        date_from=date_from_raw,
        date_to=date_to_raw,
        per_page=per_page,
        table_options=options["table_names"],
        action_options=action_options,
        source_options=source_options,
        user_options=options["users"],
    )


@audit_bp.route("/<int:audit_id>/details", methods=["GET"])
@auth_required()
def details(audit_id: int):
    """Vista de detalle para un evento de auditoria."""
    try:
        entry = AuditService.get_by_id(audit_id)
    except NotFoundError as error:
        flash(error.message, "error")
        return redirect(url_for("audit.index"))

    detail = AuditService.to_detail_view(entry)
    return render_template("admin/audit/details.html", detail=detail)
