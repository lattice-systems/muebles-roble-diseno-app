from flask import flash, redirect, render_template, request, url_for

from ...exceptions import ConflictError, NotFoundError, ValidationError
from ...models.material_category import MaterialCategory
from ...models.supplier import Supplier
from ...models.unit_of_measure import UnitOfMeasure
from .forms import RawMaterialForm, StockAdjustmentForm, WasteForm
from .services import RawMaterialService
from . import raw_materials_bp


def load_form_choices(form: RawMaterialForm) -> None:
    categories = MaterialCategory.query.order_by(MaterialCategory.name.asc()).all()
    units = UnitOfMeasure.query.order_by(UnitOfMeasure.name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()

    form.category_id.choices = [(c.id, c.name) for c in categories]
    form.unit_id.choices = [(u.id, u.name) for u in units]
    form.supplier_id.choices = [(0, "Sin proveedor")] + [
        (s.id, s.name) for s in suppliers
    ]


@raw_materials_bp.route("/")
def list_raw_materials():
    raw_materials = RawMaterialService.get_all()

    return render_template(
        "admin/raw_materials/index.html",
        raw_materials=raw_materials,
        search_term="",
        status_filter="all",
        pagination=None,
    )


@raw_materials_bp.route("/create", methods=["GET", "POST"])
def create_raw_material():
    form = RawMaterialForm()
    load_form_choices(form)

    if request.method == "POST":
        print("POST recibido en create_raw_material")  # temporal para depurar

    if form.validate_on_submit():
        try:
            RawMaterialService.create(
                {
                    "name": form.name.data,
                    "description": form.description.data,
                    "category_id": form.category_id.data,
                    "unit_id": form.unit_id.data,
                    "stock": form.stock.data,
                    "estimated_cost": form.estimated_cost.data,
                    "waste_percentage": form.waste_percentage.data,
                    "status": form.status.data,
                    "supplier_id": form.supplier_id.data or None,
                }
            )

            flash("Materia prima registrada correctamente.", "success")
            return redirect(url_for("raw_materials.list_raw_materials"))

        except (ValidationError, ConflictError) as exc:
            flash(str(exc), "danger")
    elif request.method == "POST":
        flash("Revisa los campos del formulario.", "danger")
        print(form.errors)  # temporal para depurar

    return render_template("admin/raw_materials/create.html", form=form)


@raw_materials_bp.route("/<int:raw_material_id>")
def detail_raw_material(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
    except NotFoundError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("raw_materials.list_raw_materials"))

    return render_template(
        "admin/raw_materials/details.html", raw_material=raw_material
    )


@raw_materials_bp.route("/<int:raw_material_id>/edit", methods=["GET", "POST"])
def edit_raw_material(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
    except NotFoundError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("raw_materials.list_raw_materials"))

    form = RawMaterialForm(obj=raw_material)
    load_form_choices(form)

    if request.method == "GET":
        form.category_id.data = raw_material.category_id
        form.unit_id.data = raw_material.unit_id
        form.supplier_id.data = raw_material.supplier_id or 0
        form.stock.data = raw_material.stock

    if form.validate_on_submit():
        try:
            RawMaterialService.update(
                raw_material_id,
                {
                    "name": form.name.data,
                    "description": form.description.data,
                    "category_id": form.category_id.data,
                    "unit_id": form.unit_id.data,
                    "stock": form.stock.data,
                    "estimated_cost": form.estimated_cost.data,
                    "waste_percentage": form.waste_percentage.data,
                    "status": form.status.data,
                    "supplier_id": form.supplier_id.data or None,
                },
            )

            flash("Materia prima actualizada correctamente.", "success")
            return redirect(url_for("raw_materials.list_raw_materials"))

        except (ValidationError, ConflictError) as exc:
            flash(str(exc), "danger")
    elif request.method == "POST":
        flash("Revisa los campos del formulario.", "danger")
        print(form.errors)  # temporal

    return render_template(
        "admin/raw_materials/edit.html", form=form, raw_material=raw_material
    )


@raw_materials_bp.route("/<int:raw_material_id>/toggle-status", methods=["POST"])
def toggle_status(raw_material_id: int):
    try:
        RawMaterialService.toggle_status(raw_material_id)
        flash("Estado de la materia prima actualizado correctamente.", "success")
    except (ValidationError, NotFoundError) as exc:
        flash(str(exc), "danger")

    return redirect(url_for("raw_materials.list_raw_materials"))


@raw_materials_bp.route("/<int:raw_material_id>/stock", methods=["GET", "POST"])
def adjust_stock(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
    except NotFoundError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("raw_materials.list_raw_materials"))

    form = StockAdjustmentForm()

    if form.validate_on_submit():
        try:
            RawMaterialService.adjust_stock(
                raw_material_id,
                {
                    "movement_type": form.movement_type.data,
                    "quantity": form.quantity.data,
                    "reason": form.reason.data,
                },
            )
            flash("Stock actualizado correctamente.", "success")
            return redirect(url_for("raw_materials.list_raw_materials"))
        except ValidationError as exc:
            flash(str(exc), "danger")

    return render_template(
        "admin/raw_materials/stock.html", form=form, raw_material=raw_material
    )


@raw_materials_bp.route("/<int:raw_material_id>/waste", methods=["GET", "POST"])
def update_waste(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
    except NotFoundError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("raw_materials.list_raw_materials"))

    form = WasteForm(obj=raw_material)

    if form.validate_on_submit():
        try:
            RawMaterialService.update_waste(
                raw_material_id,
                {
                    "waste_percentage": form.waste_percentage.data,
                },
            )
            flash("Merma actualizada correctamente.", "success")
            return redirect(url_for("raw_materials.list_raw_materials"))
        except ValidationError as exc:
            flash(str(exc), "danger")

    return render_template(
        "admin/raw_materials/waste.html", form=form, raw_material=raw_material
    )
