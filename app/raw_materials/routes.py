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
from app.models import MaterialCategory, UnitOfMeasure
from app.raw_materials import raw_materials_bp
from app.raw_materials.forms import RawMaterialForm, StockAdjustmentForm
from app.raw_materials.services import RawMaterialService


def _parse_selected_ids(raw_ids: str) -> list[int]:
    ids: list[int] = []
    for raw in (raw_ids or "").split(","):
        value = raw.strip()
        if not value or not value.isdigit():
            continue
        id_val = int(value)
        if id_val > 0 and id_val not in ids:
            ids.append(id_val)
    return ids


def _load_form_choices(form: RawMaterialForm) -> None:
    categories = MaterialCategory.query.order_by(MaterialCategory.name).all()
    units = UnitOfMeasure.query.order_by(UnitOfMeasure.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    form.unit_id.choices = [(u.id, f"{u.name} ({u.abbreviation})") for u in units]


@raw_materials_bp.route("/", methods=["GET"])
@auth_required()
def index():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = RawMaterialService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
        per_page=10,
    )

    # Save url for the back button
    session["raw_materials_list_url"] = request.url

    return render_template(
        "admin/raw_materials/index.html",
        raw_materials=pagination.items,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
    )


@raw_materials_bp.route("/create", methods=["GET", "POST"])
@auth_required()
def create_raw_material():
    form = RawMaterialForm()
    _load_form_choices(form)

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "category_id": form.category_id.data,
            "unit_id": form.unit_id.data,
            "waste_percentage": form.waste_percentage.data,
            "status": form.status.data,
        }

        try:
            RawMaterialService.create(data)
            flash("Materia prima creada exitosamente.", "success")
            return redirect(
                session.get("raw_materials_list_url", url_for("raw_materials.index"))
            )
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor, corrige los errores del formulario.", "error")

    return render_template("admin/raw_materials/create.html", form=form)


@raw_materials_bp.route("/<int:raw_material_id>/edit", methods=["GET", "POST"])
@auth_required()
def edit_raw_material(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(
            session.get("raw_materials_list_url", url_for("raw_materials.index"))
        )

    form = RawMaterialForm()
    _load_form_choices(form)

    if request.method == "GET":
        form.name.data = raw_material.name
        form.description.data = raw_material.description
        form.category_id.data = raw_material.category_id
        form.unit_id.data = raw_material.unit_id
        form.waste_percentage.data = raw_material.waste_percentage
        form.status.data = raw_material.status
    elif form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "category_id": form.category_id.data,
            "unit_id": form.unit_id.data,
            "waste_percentage": form.waste_percentage.data,
            "status": form.status.data,
        }

        try:
            RawMaterialService.update(raw_material_id, data)
            flash("Materia prima actualizada exitosamente.", "success")
            return redirect(
                session.get("raw_materials_list_url", url_for("raw_materials.index"))
            )
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor, corrige los errores del formulario.", "error")

    return render_template(
        "admin/raw_materials/edit.html", form=form, raw_material=raw_material
    )


@raw_materials_bp.route("/<int:raw_material_id>/details", methods=["GET"])
@auth_required()
def detail_raw_material(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        page = request.args.get("page", 1, type=int)
        movements_pagination = RawMaterialService.get_stock_movements(
            raw_material.id, page=page, per_page=15
        )

    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(
            session.get("raw_materials_list_url", url_for("raw_materials.index"))
        )

    return render_template(
        "admin/raw_materials/details.html",
        raw_material=raw_material,
        movements_pagination=movements_pagination,
    )


@raw_materials_bp.route("/<int:raw_material_id>/adjust-stock", methods=["GET", "POST"])
@auth_required()
def adjust_stock(raw_material_id: int):
    try:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(
            session.get("raw_materials_list_url", url_for("raw_materials.index"))
        )

    form = StockAdjustmentForm()

    if form.validate_on_submit():
        try:
            RawMaterialService.adjust_stock(
                raw_material_id=raw_material.id,
                movement_type=form.movement_type.data,
                quantity=form.quantity.data,
                reason=form.reason.data,
            )
            flash("Inventario ajustado correctamente.", "success")
            return redirect(
                url_for(
                    "raw_materials.detail_raw_material", raw_material_id=raw_material.id
                )
            )
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    return render_template(
        "admin/raw_materials/adjust_stock.html", form=form, raw_material=raw_material
    )


@raw_materials_bp.route("/<int:raw_material_id>/toggle-status", methods=["POST"])
@auth_required()
def toggle_status(raw_material_id: int):
    try:
        new_status = RawMaterialService.toggle_status(raw_material_id)
        flash(
            "Materia prima activada." if new_status else "Materia prima desactivada.",
            "success",
        )
    except NotFoundError as e:
        flash(e.message, "error")

    return redirect(
        session.get("raw_materials_list_url", url_for("raw_materials.index"))
    )


@raw_materials_bp.route("/bulk-action", methods=["POST"])
@auth_required()
def bulk_action_raw_materials():
    action = (request.form.get("action") or "").strip().lower()
    selected_ids = _parse_selected_ids(request.form.get("selected_ids", ""))

    fallback_url = session.get("raw_materials_list_url", url_for("raw_materials.index"))

    if not selected_ids:
        flash("Selecciona al menos una materia prima", "error")
        return redirect(fallback_url)

    if action == "export":
        raw_materials_list = RawMaterialService.get_by_ids(selected_ids)
        if not raw_materials_list:
            flash("No se encontraron materias primas para exportar", "error")
            return redirect(fallback_url)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Nombre",
                "Categoría",
                "Unidad",
                "Stock",
                "Merma %",
                "Estado",
                "Fecha Registro",
            ]
        )
        for rm in raw_materials_list:
            writer.writerow(
                [
                    rm.id,
                    rm.name,
                    rm.category.name if rm.category else "",
                    rm.unit.name if rm.unit else "",
                    rm.stock,
                    rm.waste_percentage,
                    "Activo" if rm.status == "active" else "Inactivo",
                    (
                        rm.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(rm, "created_at") and rm.created_at
                        else ""
                    ),
                ]
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=materias_primas_{timestamp}.csv"
        )
        return response

    if action in {"activate", "deactivate"}:
        target_status = action == "activate"
        result = RawMaterialService.bulk_set_status(
            selected_ids, target_status=target_status
        )

        updated = result["updated"]
        not_found = result["not_found"]

        action_text = "activadas" if target_status else "desactivadas"
        flash(f"{updated} materia(s) prima(s) {action_text}.", "success")
        if not_found:
            flash(f"{not_found} materia(s) prima(s) no encontrada(s).", "error")

        return redirect(fallback_url)

    flash("Acción masiva inválida", "error")
    return redirect(fallback_url)
