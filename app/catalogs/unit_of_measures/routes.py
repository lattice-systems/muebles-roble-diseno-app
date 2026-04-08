"""
Rutas/Endpoints para el módulo de unidades de medida.
"""

import csv
from datetime import datetime
from io import StringIO
from flask import flash, redirect, render_template, request, url_for, make_response
from flask_security import auth_required

from . import unit_of_measures_bp
from .forms import UnitOfMeasureForm
from .services import UnitOfMeasureService
from app.exceptions import ConflictError, NotFoundError, ValidationError


@unit_of_measures_bp.route("/", methods=["GET"])
@auth_required()
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
@auth_required()
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
@auth_required()
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
@auth_required()
def delete_unit_of_measure(id_unit_of_measure: int):
    try:
        # Re-using delete as a toggle to fit the toggle button logic.
        UnitOfMeasureService.toggle_status(id_unit_of_measure)
        flash("Estado de la unidad de medida actualizado exitosamente", "success")
    except NotFoundError:
        flash("Unidad de medida no encontrada", "error")

    return redirect(url_for("unit_of_measures.list_unit_of_measures"))


@unit_of_measures_bp.route("/bulk-activate", methods=["POST"])
@auth_required()
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
@auth_required()
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


@unit_of_measures_bp.route("/bulk-export", methods=["POST"])
@auth_required()
def bulk_export():
    """Exportar múltiples unidades de medida seleccionadas a CSV."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("unit_of_measures.list_unit_of_measures"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    units = UnitOfMeasureService.get_by_ids(ids)
    if not units:
        flash("No se encontraron registros para exportar", "error")
        return redirect(url_for("unit_of_measures.list_unit_of_measures"))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Abreviatura", "Tipo", "Estado"])
    for u in units:
        writer.writerow(
            [
                u.id_unit_of_measure,
                u.name,
                u.abbreviation,
                u.type,
                "Activo" if u.status else "Inactivo",
            ]
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="unidades_medida_{timestamp}.csv"'
    )
    return response
