"""Rutas para gestionar notificaciones del navbar."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_security import auth_required

from app.notifications import notifications_bp
from app.shared.navbar_notifications import (
    build_navbar_notifications,
    dismiss_notification,
    dismiss_notifications,
)


@notifications_bp.route("/", methods=["GET"])
@auth_required()
def index():
    """Muestra la bandeja de notificaciones recientes."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    allowed_per_page = {10, 20, 50}
    if per_page not in allowed_per_page:
        per_page = 10

    feed = build_navbar_notifications(limit=50, include_dismissed=False)
    notifications = feed["items"]

    start = max(0, (page - 1) * per_page)
    end = start + per_page
    page_items = notifications[start:end]

    total = len(notifications)
    has_prev = start > 0
    has_next = end < total

    return render_template(
        "admin/notifications/index.html",
        notifications=page_items,
        page=page,
        per_page=per_page,
        total=total,
        has_prev=has_prev,
        has_next=has_next,
        prev_page=max(1, page - 1),
        next_page=page + 1,
    )


@notifications_bp.route("/dismiss/<source_kind>/<int:source_id>", methods=["POST"])
@auth_required()
def dismiss(source_kind: str, source_id: int):
    """Descarta una notificacion puntual para el usuario actual."""
    if dismiss_notification(source_kind, source_id):
        flash("Notificacion eliminada.", "success")
    else:
        flash("La notificacion ya habia sido eliminada.", "info")

    return redirect(request.referrer or url_for("notifications.index"))


@notifications_bp.route("/clear", methods=["POST"])
@auth_required()
def clear():
    """Descarta todas las notificaciones visibles."""
    feed = build_navbar_notifications(limit=50, include_dismissed=False)
    removed_count = dismiss_notifications(feed["items"])
    flash(
        (
            f"Se eliminaron {removed_count} notificaciones."
            if removed_count
            else "No habia notificaciones para eliminar."
        ),
        "success" if removed_count else "info",
    )
    return redirect(request.referrer or url_for("notifications.index"))
