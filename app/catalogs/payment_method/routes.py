"""
Rutas/Endpoints para el módulo de métodos de pago.
"""

import csv
from datetime import datetime
from io import StringIO
from flask import flash, redirect, render_template, request, url_for, make_response

from app.exceptions import ConflictError, NotFoundError, ValidationError

from . import payment_method_bp
from .forms import PaymentMethodForm
from .services import PaymentMethodService


@payment_method_bp.route("/", methods=["GET"])
def list_payment_method():
    """
    Muestra la lista de métodos de pago con búsqueda, filtro y paginación.
    """
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = PaymentMethodService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
    )

    form = PaymentMethodForm()

    return render_template(
        "admin/payment_method/index.html",
        payment_methods=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
    )


@payment_method_bp.route("/create", methods=["POST"])
def create_payment_method():
    """
    Crea un nuevo método de pago desde el modal.
    POST: Valida, crea y redirige. En error, re-renderiza con modal abierto.
    """
    form = PaymentMethodForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "type": form.type.data,
            "description": form.description.data,
            "status": request.form.get("status", "1"),
            "available_pos": request.form.get("available_pos", "true"),
            "available_ecommerce": request.form.get("available_ecommerce", "true"),
        }
        try:
            PaymentMethodService.create(data)
            flash("Método de pago creado exitosamente", "success")
            return redirect(url_for("payment_method.list_payment_method"))
        except (ConflictError, ValidationError) as e:
            flash(e.message, "error")

    # Re-render list with modal open on validation error
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    pagination = PaymentMethodService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
    )
    return render_template(
        "admin/payment_method/index.html",
        payment_methods=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
        show_create_modal=True,
    )


@payment_method_bp.route("/<int:id_payment_method>/edit", methods=["POST"])
def edit_payment_method(id_payment_method: int):
    """
    Edita un método de pago desde el modal.
    POST: Valida, actualiza y redirige. En error, re-renderiza con modal abierto.
    """
    form = PaymentMethodForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "type": form.type.data,
            "description": form.description.data,
            "status": request.form.get("status", "1"),
            "available_pos": request.form.get("available_pos", "true"),
            "available_ecommerce": request.form.get("available_ecommerce", "true"),
        }
        try:
            PaymentMethodService.update(id_payment_method, data)
            flash("Método de pago actualizado exitosamente", "success")
            return redirect(url_for("payment_method.list_payment_method"))
        except (ConflictError, ValidationError, NotFoundError) as e:
            flash(e.message, "error")

    # Re-render list with edit modal open on validation error
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    pagination = PaymentMethodService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
    )
    return render_template(
        "admin/payment_method/index.html",
        payment_methods=pagination.items,
        pagination=pagination,
        form=form,
        edit_form=form,
        search_term=search_term,
        status_filter=status_filter,
        show_edit_modal=id_payment_method,
    )


@payment_method_bp.route("/<int:id_payment_method>/delete", methods=["POST"])
def delete_payment_method(id_payment_method: int):
    """
    Toggle de estado de un método de pago (desactivar/activar).
    """
    try:
        PaymentMethodService.delete(id_payment_method)
        flash("Estado del método de pago actualizado exitosamente", "success")
    except NotFoundError as e:
        flash(e.message, "error")

    return redirect(url_for("payment_method.list_payment_method"))


@payment_method_bp.route("/bulk-deactivate", methods=["POST"])
def bulk_deactivate():
    """Desactivar múltiples métodos de pago seleccionados."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron métodos de pago", "error")
        return redirect(url_for("payment_method.list_payment_method"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    count = PaymentMethodService.bulk_deactivate(ids)
    flash(f"{count} método(s) de pago desactivado(s) exitosamente", "success")
    return redirect(url_for("payment_method.list_payment_method"))


@payment_method_bp.route("/bulk-activate", methods=["POST"])
def bulk_activate():
    """Activar múltiples métodos de pago seleccionados."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron métodos de pago", "error")
        return redirect(url_for("payment_method.list_payment_method"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    count = PaymentMethodService.bulk_activate(ids)
    flash(f"{count} método(s) de pago activado(s) exitosamente", "success")
    return redirect(url_for("payment_method.list_payment_method"))


@payment_method_bp.route("/bulk-export", methods=["POST"])
def bulk_export():
    """Exportar múltiples métodos de pago seleccionados a CSV."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron métodos de pago", "error")
        return redirect(url_for("payment_method.list_payment_method"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    payment_methods = PaymentMethodService.get_by_ids(ids)
    if not payment_methods:
        flash("No se encontraron registros para exportar", "error")
        return redirect(url_for("payment_method.list_payment_method"))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Tipo", "Estado", "POS", "Ecommerce", "Descripcion"])
    for p in payment_methods:
        writer.writerow([
            p.id,
            p.name,
            p.type,
            "Activo" if p.status else "Inactivo",
            "Si" if p.available_pos else "No",
            "Si" if p.available_ecommerce else "No",
            p.description or ""
        ])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepend BOM so Excel properly recognizes UTF-8 formatting
    csv_data = '\ufeff' + output.getvalue()

    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="metodos_pago_{timestamp}.csv"'
    return response
