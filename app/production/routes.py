"""
Rutas y controladores para Producción y Recetas (BOM).
"""

from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_security import auth_required, current_user

from app.exceptions import ConflictError, NotFoundError, ValidationError

from . import production_bp
from .forms import BomForm, ProductionOrderForm, ProductionStatusForm
from .services import ProductionService


def _parse_bom_items_from_request() -> list[dict]:
    raw_material_ids = request.form.getlist("raw_material_id[]")
    quantities = request.form.getlist("quantity_required[]")

    items: list[dict] = []
    for idx, raw_material_id in enumerate(raw_material_ids):
        raw_material_id = (raw_material_id or "").strip()
        quantity = (quantities[idx] if idx < len(quantities) else "").strip()

        if not raw_material_id and not quantity:
            continue

        items.append(
            {
                "raw_material_id": raw_material_id,
                "quantity_required": quantity,
            }
        )

    return items


def _parse_material_updates_from_request() -> list[dict]:
    raw_material_ids = request.form.getlist("raw_material_id[]")
    quantities_used = request.form.getlist("quantity_used[]")
    waste_applied = request.form.getlist("waste_applied[]")

    rows: list[dict] = []
    for idx, raw_material_id in enumerate(raw_material_ids):
        raw_material_id = (raw_material_id or "").strip()
        if not raw_material_id:
            continue

        rows.append(
            {
                "raw_material_id": raw_material_id,
                "quantity_used": (
                    quantities_used[idx] if idx < len(quantities_used) else "0"
                ),
                "waste_applied": (
                    waste_applied[idx] if idx < len(waste_applied) else "0"
                ),
            }
        )

    return rows


@production_bp.route("/", methods=["GET"])
@auth_required()
def orders_index():
    """Listado de órdenes de producción."""
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all").strip() or "all"
    page = request.args.get("page", 1, type=int)

    pagination = ProductionService.get_production_orders(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
        per_page=10,
    )

    return render_template(
        "admin/production/orders_index.html",
        orders=pagination.items,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
    )


@production_bp.route("/orders/create", methods=["GET", "POST"])
@auth_required()
def create_order():
    """Crea una orden de producción manual."""
    form = ProductionOrderForm()
    form.product_id.choices = ProductionService.get_product_choices()

    if request.method == "GET" and not form.scheduled_date.data:
        form.scheduled_date.data = date.today()

    if form.validate_on_submit():
        try:
            order = ProductionService.create_production_order(
                product_id=form.product_id.data,
                quantity=form.quantity.data,
                scheduled_date=form.scheduled_date.data,
                user_id=current_user.id,
            )
            flash("Orden de producción creada correctamente", "success")
            return redirect(url_for("production.order_details", order_id=order.id))
        except (ValidationError, ConflictError, NotFoundError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    return render_template("admin/production/create_order.html", form=form)


@production_bp.route("/orders/<int:order_id>/details", methods=["GET"])
@auth_required()
def order_details(order_id: int):
    """Detalle de orden de producción con consumos."""
    try:
        order = ProductionService.get_production_order_by_id(order_id)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("production.orders_index"))

    status_form = ProductionStatusForm()
    allowed_statuses = ProductionService.get_allowed_status_transitions(order)
    status_form.status.choices = [
        (status, status.replace("_", " ").title()) for status in allowed_statuses
    ] or [(order.status, order.status.replace("_", " ").title())]
    status_form.status.data = order.status

    return render_template(
        "admin/production/order_details.html",
        order=order,
        status_form=status_form,
        allowed_statuses=allowed_statuses,
    )


@production_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@auth_required()
def update_order_status(order_id: int):
    """Actualiza el estado de una orden de producción."""
    form = ProductionStatusForm()
    if not form.validate_on_submit():
        flash("El estado enviado no es válido", "error")
        return redirect(url_for("production.order_details", order_id=order_id))

    try:
        ProductionService.change_production_order_status(
            production_order_id=order_id,
            new_status=form.status.data,
            user_id=current_user.id,
        )
        flash("Estado de producción actualizado", "success")
    except (ValidationError, ConflictError, NotFoundError) as e:
        flash(e.message, "error")

    return redirect(url_for("production.order_details", order_id=order_id))


@production_bp.route("/orders/<int:order_id>/materials", methods=["POST"])
@auth_required()
def update_order_materials(order_id: int):
    """Registra consumo real para los materiales de una orden."""
    try:
        rows = _parse_material_updates_from_request()
        ProductionService.update_material_usage(
            production_order_id=order_id,
            materials_data=rows,
            user_id=current_user.id,
        )
        flash("Consumos de materiales actualizados", "success")
    except (ValidationError, ConflictError, NotFoundError) as e:
        flash(e.message, "error")

    return redirect(url_for("production.order_details", order_id=order_id))


@production_bp.route("/boms", methods=["GET"])
@auth_required()
def boms_index():
    """Listado de recetas BOM."""
    search_term = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    pagination = ProductionService.get_boms(
        search_term=search_term or None,
        page=page,
        per_page=10,
    )

    return render_template(
        "admin/production/boms_index.html",
        boms=pagination.items,
        pagination=pagination,
        search_term=search_term,
    )


@production_bp.route("/boms/create", methods=["GET", "POST"])
@auth_required()
def create_bom():
    """Crea una receta BOM nueva."""
    form = BomForm()
    form.product_id.choices = ProductionService.get_product_choices()
    raw_material_choices = ProductionService.get_raw_material_choices()

    if form.validate_on_submit():
        try:
            items_data = _parse_bom_items_from_request()
            bom = ProductionService.create_bom(
                product_id=form.product_id.data,
                version=form.version.data,
                description=form.description.data,
                items_data=items_data,
                user_id=current_user.id,
            )
            flash("Receta creada correctamente", "success")
            return redirect(url_for("production.bom_details", bom_id=bom.id))
        except (ValidationError, ConflictError, NotFoundError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    return render_template(
        "admin/production/create_bom.html",
        form=form,
        raw_material_choices=raw_material_choices,
    )


@production_bp.route("/boms/<int:bom_id>/details", methods=["GET"])
@auth_required()
def bom_details(bom_id: int):
    """Detalle de receta BOM."""
    try:
        bom = ProductionService.get_bom_by_id(bom_id)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("production.boms_index"))

    return render_template("admin/production/bom_details.html", bom=bom)


@production_bp.route("/boms/<int:bom_id>/edit", methods=["GET", "POST"])
@auth_required()
def edit_bom(bom_id: int):
    """Edita una receta BOM."""
    try:
        bom = ProductionService.get_bom_by_id(bom_id)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("production.boms_index"))

    form = BomForm()
    form.product_id.choices = ProductionService.get_product_choices(
        include_inactive_id=bom.product_id
    )

    current_material_ids = [item.raw_material_id for item in bom.items]
    raw_material_choices = ProductionService.get_raw_material_choices(
        include_inactive_ids=current_material_ids
    )

    if request.method == "GET":
        form.product_id.data = bom.product_id
        form.version.data = bom.version
        form.description.data = bom.description
    elif request.method == "POST":
        # El producto no es editable en esta vista (campo disabled en UI);
        # lo fijamos desde el BOM para evitar errores de validación por campo faltante.
        form.product_id.data = bom.product_id

        if form.validate_on_submit():
            try:
                items_data = _parse_bom_items_from_request()
                ProductionService.update_bom(
                    bom_id=bom.id,
                    version=form.version.data,
                    description=form.description.data,
                    items_data=items_data,
                    user_id=current_user.id,
                )
                flash("Receta actualizada correctamente", "success")
                return redirect(url_for("production.bom_details", bom_id=bom.id))
            except (ValidationError, ConflictError, NotFoundError) as e:
                flash(e.message, "error")
        else:
            flash("Por favor corrige los errores del formulario", "error")

    return render_template(
        "admin/production/edit_bom.html",
        form=form,
        bom=bom,
        raw_material_choices=raw_material_choices,
    )
