"""
Rutas y controladores para el flujo de compras (Purchase Orders).
"""

import csv
from datetime import datetime
from io import StringIO

from flask import (
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_security import auth_required

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.purchases import purchases_bp
from app.purchases.forms import PurchaseOrderForm
from app.purchases.services import PurchaseOrderService


def _parse_selected_ids(raw_ids: str) -> list[int]:
    """Toma un string de IDs separados por coma y devuelve una lista de enteros únicos."""
    ids: list[int] = []
    for raw in (raw_ids or "").split(","):
        value = raw.strip()
        if not value or not value.isdigit():
            continue
        id_val = int(value)
        if id_val > 0 and id_val not in ids:
            ids.append(id_val)
    return ids


@purchases_bp.route("/", methods=["GET"])
@auth_required()
def index():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "pendiente")
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    sort_by = request.args.get("sort", "date_desc")
    page = request.args.get("page", 1, type=int)

    pagination = PurchaseOrderService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        date_from=date_from or None,
        date_to=date_to or None,
        sort_by=sort_by,
        page=page,
        per_page=10,
    )

    session["purchases_list_url"] = request.url

    return render_template(
        "admin/purchases/index.html",
        orders=pagination.items,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
    )


@purchases_bp.route("/create", methods=["GET", "POST"])
@auth_required()
def create_order():
    form = PurchaseOrderForm()
    form.supplier_id.choices = PurchaseOrderService.get_supplier_choices()
    raw_materials_choices = PurchaseOrderService.get_raw_material_choices()

    if form.validate_on_submit():
        # Extraemos los arreglos provenientes del formulario dinámico de ítems
        rm_ids = request.form.getlist("raw_material_id[]")
        quantities = request.form.getlist("quantity[]")
        conversion_factors = request.form.getlist("conversion_factor[]")
        prices = request.form.getlist("unit_price[]")

        items_data = []
        for i in range(len(rm_ids)):
            items_data.append(
                {
                    "raw_material_id": int(rm_ids[i]),
                    "quantity": float(quantities[i]) if quantities[i] else 0,
                    "conversion_factor": (
                        float(conversion_factors[i])
                        if i < len(conversion_factors) and conversion_factors[i]
                        else 1.0
                    ),
                    "unit_price": float(prices[i]) if prices[i] else 0,
                }
            )

        data = {
            "supplier_id": form.supplier_id.data,
            "order_date": form.order_date.data,
        }

        try:
            PurchaseOrderService.create(data, items_data)
            flash("Orden de compra creada exitosamente", "success")
            return redirect(url_for("purchases.index"))
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    if not form.supplier_id.choices:
        flash("No hay proveedores activos para asignar a la orden", "error")

    return render_template(
        "admin/purchases/create.html",
        form=form,
        raw_materials_choices=raw_materials_choices,
    )


@purchases_bp.route("/<int:id_order>/edit", methods=["GET", "POST"])
@auth_required()
def edit_order(id_order: int):
    try:
        order = PurchaseOrderService.get_by_id(id_order)
        if order.status != "pendiente":
            flash("Solo se pueden editar órdenes en estado 'pendiente'", "error")
            return redirect(url_for("purchases.index"))
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("purchases.index"))

    form = PurchaseOrderForm()
    form.supplier_id.choices = PurchaseOrderService.get_supplier_choices(
        include_inactive_id=order.supplier_id
    )
    current_material_ids = [item.raw_material_id for item in order.items]
    raw_materials_choices = PurchaseOrderService.get_raw_material_choices(
        include_inactive_ids=current_material_ids
    )

    if request.method == "GET":
        form.supplier_id.data = order.supplier_id
        form.order_date.data = order.order_date
    elif form.validate_on_submit():
        rm_ids = request.form.getlist("raw_material_id[]")
        quantities = request.form.getlist("quantity[]")
        conversion_factors = request.form.getlist("conversion_factor[]")
        prices = request.form.getlist("unit_price[]")

        items_data = []
        for i in range(len(rm_ids)):
            items_data.append(
                {
                    "raw_material_id": int(rm_ids[i]),
                    "quantity": float(quantities[i]) if quantities[i] else 0,
                    "conversion_factor": (
                        float(conversion_factors[i])
                        if i < len(conversion_factors) and conversion_factors[i]
                        else 1.0
                    ),
                    "unit_price": float(prices[i]) if prices[i] else 0,
                }
            )

        data = {
            "supplier_id": form.supplier_id.data,
            "order_date": form.order_date.data,
        }

        try:
            PurchaseOrderService.update(id_order, data, items_data)
            flash("Orden de compra actualizada exitosamente", "success")
            return redirect(url_for("purchases.detail_order", id_order=id_order))
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    return render_template(
        "admin/purchases/edit.html",
        form=form,
        order=order,
        raw_materials_choices=raw_materials_choices,
    )


@purchases_bp.route("/<int:id_order>/details", methods=["GET"])
@auth_required()
def detail_order(id_order: int):
    try:
        order = PurchaseOrderService.get_by_id(id_order)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("purchases.index"))

    return render_template("admin/purchases/details.html", order=order)


@purchases_bp.route("/<int:id_order>/change-status", methods=["POST"])
@auth_required()
def change_status_order(id_order: int):
    new_status = request.form.get("status")

    received_qtys_raw = request.form.getlist("received_qty[]")
    received_qtys = []
    for qty in received_qtys_raw:
        try:
            received_qtys.append(float(qty))
        except ValueError:
            received_qtys.append(0.0)

    try:
        order = PurchaseOrderService.change_status(
            id_order, new_status, received_qtys=received_qtys
        )
        flash(f"La orden ahora se encuentra en estado '{order.status}'", "success")
    except (NotFoundError, ConflictError, ValidationError) as e:
        flash(e.message, "error")

    # Mantenemos al usuario en la misma vista de detalle de la orden
    return redirect(url_for("purchases.detail_order", id_order=id_order))


@purchases_bp.route("/<int:id_order>/delete", methods=["POST"])
@auth_required()
def delete_order(id_order: int):
    search_term = request.form.get("q", "").strip()
    status_filter = request.form.get("status", "pendiente")
    date_from = request.form.get("date_from", "").strip()
    date_to = request.form.get("date_to", "").strip()
    sort_by = request.form.get("sort", "date_desc")
    page_raw = request.form.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1

    try:
        PurchaseOrderService.delete(id_order)
        flash("Orden de compra eliminada exitosamente", "success")
    except (NotFoundError, ConflictError) as e:
        flash(e.message, "error")

    return redirect(
        url_for(
            "purchases.index",
            page=page,
            q=search_term,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            sort=sort_by,
        )
    )


@purchases_bp.route("/bulk-action", methods=["POST"])
@auth_required()
def bulk_action_orders():
    search_term = request.form.get("q", "").strip()
    status_filter = request.form.get("status", "pendiente")
    date_from = request.form.get("date_from", "").strip()
    date_to = request.form.get("date_to", "").strip()
    sort_by = request.form.get("sort", "date_desc")
    page_raw = request.form.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1

    action = (request.form.get("action") or "").strip().lower()
    selected_ids = _parse_selected_ids(request.form.get("selected_ids", ""))

    if not selected_ids:
        flash("Selecciona al menos una orden de compra", "error")
        return redirect(
            url_for(
                "purchases.index",
                page=page,
                q=search_term,
                status=status_filter,
                date_from=date_from,
                date_to=date_to,
                sort=sort_by,
            )
        )

    if action == "export":
        orders = PurchaseOrderService.get_by_ids(selected_ids)
        if not orders:
            flash("No se encontraron órdenes para exportar", "error")
            return redirect(
                url_for(
                    "purchases.index",
                    page=page,
                    q=search_term,
                    status=status_filter,
                    date_from=date_from,
                    date_to=date_to,
                    sort=sort_by,
                )
            )

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Folio OC",
                "Proveedor",
                "Fecha de Orden",
                "Estado",
                "Total",
                "Fecha de registro",
            ]
        )
        for order in orders:
            writer.writerow(
                [
                    order.id,
                    order.supplier.name if order.supplier else "N/A",
                    order.order_date.isoformat() if order.order_date else "",
                    order.status.capitalize(),
                    f"{order.total:.2f}",
                    (
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(order, "created_at") and order.created_at
                        else ""
                    ),
                ]
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=ordenes_compra_{timestamp}.csv"
        )
        return response

    flash("Acción masiva inválida", "error")
    return redirect(
        url_for(
            "purchases.index",
            page=page,
            q=search_term,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            sort=sort_by,
        )
    )
