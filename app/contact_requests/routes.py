"""Rutas internas para seguimiento de solicitudes de contacto/cita."""

from flask import flash, redirect, render_template, request, url_for
from flask_security import auth_required, current_user

from app.models.contact_request import ContactRequest

from . import contact_requests_bp
from .services import ContactRequestService


@contact_requests_bp.route("/", methods=["GET"])
@auth_required()
def index():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all").strip() or "all"
    type_filter = request.args.get("type", "all").strip() or "all"
    page = request.args.get("page", 1, type=int)

    pagination = ContactRequestService.get_requests(
        search_term=search_term,
        status=status_filter,
        request_type=type_filter,
        page=page,
        per_page=12,
    )

    return render_template(
        "admin/contact_requests/index.html",
        requests=pagination.items,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
        type_filter=type_filter,
        summary_metrics=ContactRequestService.get_summary_metrics(),
        status_options=ContactRequest.VALID_STATUSES,
        status_labels=ContactRequest.STATUS_LABELS,
        type_options=ContactRequest.VALID_TYPES,
        type_labels=ContactRequest.TYPE_LABELS,
    )


@contact_requests_bp.route("/<int:request_id>", methods=["GET"])
@auth_required()
def detail(request_id: int):
    contact_request = ContactRequestService.get_request_or_404(request_id)

    return render_template(
        "admin/contact_requests/detail.html",
        contact_request=contact_request,
        status_options=ContactRequest.VALID_STATUSES,
        status_labels=ContactRequest.STATUS_LABELS,
        type_labels=ContactRequest.TYPE_LABELS,
        conversion_defaults=ContactRequestService.get_conversion_defaults(
            contact_request
        ),
    )


@contact_requests_bp.route("/<int:request_id>/assign", methods=["POST"])
@auth_required()
def assign_to_me(request_id: int):
    ContactRequestService.assign_to_user(request_id=request_id, user_id=current_user.id)
    flash("Solicitud asignada correctamente.", "success")
    return redirect(url_for("contact_requests.detail", request_id=request_id))


@contact_requests_bp.route("/<int:request_id>/status", methods=["POST"])
@auth_required()
def update_status(request_id: int):
    status = request.form.get("status", "")
    notes = request.form.get("internal_notes", "")

    try:
        ContactRequestService.update_status(
            request_id,
            status=status,
            internal_notes=notes,
        )
        flash("Estado de la solicitud actualizado.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("contact_requests.detail", request_id=request_id))


@contact_requests_bp.route("/<int:request_id>/convert", methods=["POST"])
@auth_required()
def convert_to_special_order(request_id: int):
    form_data = {
        "product_name": request.form.get("product_name", ""),
        "quantity": request.form.get("quantity", ""),
        "unit_price": request.form.get("unit_price", ""),
        "estimated_delivery_date": request.form.get("estimated_delivery_date", ""),
        "phone": request.form.get("phone", ""),
        "notes": request.form.get("notes", ""),
    }

    try:
        order = ContactRequestService.convert_to_special_order(
            request_id,
            form_data=form_data,
            user_id=current_user.id,
        )
        flash(f"Solicitud convertida a orden especial #{order.id}.", "success")
        return redirect(url_for("customer_orders.detail", order_id=order.id))
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("contact_requests.detail", request_id=request_id))
