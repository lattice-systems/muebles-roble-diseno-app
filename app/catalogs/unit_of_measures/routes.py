"""
Rutas/Endpoints para el módulo de unidades de medida.
"""

from flask import flash, redirect, render_template, request, url_for

from . import unit_of_measures_bp
from .forms import UnitOfMeasureForm
from .services import UnitOfMeasureService
from app.exceptions import ConflictError, NotFoundError, ValidationError


@unit_of_measures_bp.route("/", methods=["GET"])
def list_unit_of_measures():
    """
    Muestra la lista de unidades de medida del catálogo filtrada y paginada.
    """
    search_term = request.args.get("q", "")
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = UnitOfMeasureService.get_all(
        search_term=search_term, status_filter=status_filter, page=page
    )
    form = UnitOfMeasureForm()

    return render_template(
        "admin/unit_of_measures/index.html",
        units_of_measures=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
    )


@unit_of_measures_bp.route("/create", methods=["POST"])
def create_unit_of_measure():
    form = UnitOfMeasureForm()

    if form.validate_on_submit():
        raw_status = request.form.get("status", "1")
        data = {
            "name": form.name.data,
            "abbreviation": form.abbreviation.data,
            "type": form.type.data,
            "active": bool(int(raw_status)) if raw_status.isdigit() else True,
        }
        try:
            UnitOfMeasureService.create(data)
            flash("Unidad de medida creada exitosamente", "success")
            return redirect(url_for("unit_of_measures.list_unit_of_measures"))
        except (ConflictError, ValidationError) as e:
            flash(str(e), "error")

    search_term = request.args.get("q", "")
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = UnitOfMeasureService.get_all(
        search_term=search_term, status_filter=status_filter, page=page
    )
    return render_template(
        "admin/unit_of_measures/index.html",
        units_of_measures=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
        show_create_modal=True,
    )


@unit_of_measures_bp.route("/<int:id_unit_of_measure>/edit", methods=["POST"])
def edit_unit_of_measure(id_unit_of_measure):
    form = UnitOfMeasureForm()

    if form.validate_on_submit():
        raw_status = request.form.get("status", "1")
        data = {
            "name": form.name.data,
            "abbreviation": form.abbreviation.data,
            "type": form.type.data,
            "active": bool(int(raw_status)) if raw_status.isdigit() else True,
        }
        try:
            UnitOfMeasureService.update(id_unit_of_measure, data)
            flash("Unidad de medida actualizada exitosamente", "success")
            return redirect(url_for("unit_of_measures.list_unit_of_measures"))
        except (ConflictError, ValidationError) as e:
            flash(str(e), "error")

    search_term = request.args.get("q", "")
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = UnitOfMeasureService.get_all(
        search_term=search_term, status_filter=status_filter, page=page
    )
    blank_form = UnitOfMeasureForm()
    return render_template(
        "admin/unit_of_measures/index.html",
        units_of_measures=pagination.items,
        pagination=pagination,
        form=blank_form,
        edit_form=form,
        search_term=search_term,
        status_filter=status_filter,
        show_edit_modal=id_unit_of_measure,
    )


@unit_of_measures_bp.route("/<int:id_unit_of_measure>/delete", methods=["POST"])
def delete_unit_of_measure(id_unit_of_measure: int):
    try:
        # Re-using delete as a toggle to fit the toggle button logic.
        UnitOfMeasureService.toggle_status(id_unit_of_measure)
        flash("Estado de la unidad de medida actualizado exitosamente", "success")
    except NotFoundError:
        flash("Unidad de medida no encontrada", "error")

    return redirect(url_for("unit_of_measures.list_unit_of_measures"))


@unit_of_measures_bp.route("/bulk-activate", methods=["POST"])
def bulk_activate_unit_of_measures():
    ids_str = request.form.get("ids", "")
    if ids_str:
        ids = [int(i.strip()) for i in ids_str.split(",") if i.strip().isdigit()]
        if ids:
            try:
                UnitOfMeasureService.bulk_toggle_status(ids, True)
                flash(
                    f"{len(ids)} unidades de medida activadas exitosamente", "success"
                )
            except Exception as e:
                flash(f"Error al activar unidades de medida: {e}", "error")
    return redirect(url_for("unit_of_measures.list_unit_of_measures"))


@unit_of_measures_bp.route("/bulk-deactivate", methods=["POST"])
def bulk_deactivate_unit_of_measures():
    ids_str = request.form.get("ids", "")
    if ids_str:
        ids = [int(i.strip()) for i in ids_str.split(",") if i.strip().isdigit()]
        if ids:
            try:
                UnitOfMeasureService.bulk_toggle_status(ids, False)
                flash(
                    f"{len(ids)} unidades de medida desactivadas exitosamente",
                    "success",
                )
            except Exception as e:
                flash(f"Error al desactivar unidades de medida: {e}", "error")
    return redirect(url_for("unit_of_measures.list_unit_of_measures"))
