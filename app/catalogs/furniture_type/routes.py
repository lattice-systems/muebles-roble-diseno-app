"""
Rutas/Endpoints para el módulo de tipo de mueble.
"""

import csv
from datetime import datetime
from io import StringIO
from flask import flash, redirect, render_template, request, url_for, make_response
from flask_security import auth_required
from . import furniture_type_bp
from .forms import FurnitureTypeForm
from .services import FurnitureTypeService
from app.exceptions import ConflictError


@furniture_type_bp.route("/", methods=["GET"])
@auth_required()
def list_furniture_type():
    """
    Muestra la lista de tipo de mueble del catálogo.
    """
    search_term = request.args.get("q", "")
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = FurnitureTypeService.get_all(
        search_term=search_term, status_filter=status_filter, page=page
    )
    form = FurnitureTypeForm()

    return render_template(
        "admin/furniture_types/index.html",
        furniture_types=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
    )


@furniture_type_bp.route("/create", methods=["POST"])
@auth_required()
def create_furniture_type():
    """
    Crea un nuevo tipo de mueble en el catálogo.
    """
    form = FurnitureTypeForm()

    if form.validate_on_submit():
        raw_status = request.form.get("status", "1")
        data = {
            "title": form.title.data,
            "status": bool(int(raw_status)) if raw_status.isdigit() else True,
        }
        try:
            FurnitureTypeService.create(data)
            flash("Tipo de mueble creado exitosamente", "success")
            return redirect(url_for("furniture_type.list_furniture_type"))
        except ConflictError as e:
            flash(e.message, "error")

    pagination = FurnitureTypeService.get_all()
    return render_template(
        "admin/furniture_types/index.html",
        furniture_types=pagination.items,
        pagination=pagination,
        form=form,
        show_create_modal=True,
    )


@furniture_type_bp.route("/<int:id_furniture_type>/edit", methods=["POST"])
@auth_required()
def edit_furniture_type(id_furniture_type: int):
    """
    Actualiza un tipo de mueble existente manejado a través de modales.
    """
    form = FurnitureTypeForm()

    if form.validate_on_submit():
        raw_status = request.form.get("status", "1")
        data = {
            "title": form.title.data,
            "status": bool(int(raw_status)) if raw_status.isdigit() else True,
        }
        try:
            FurnitureTypeService.update(id_furniture_type, data)
            flash("Tipo de mueble actualizado exitosamente", "success")
            return redirect(url_for("furniture_type.list_furniture_type"))
        except ConflictError as e:
            flash(e.message, "error")

    pagination = FurnitureTypeService.get_all()
    blank_form = FurnitureTypeForm()
    return render_template(
        "admin/furniture_types/index.html",
        furniture_types=pagination.items,
        pagination=pagination,
        form=blank_form,
        edit_form=form,
        show_edit_modal=id_furniture_type,
    )


@furniture_type_bp.route("/<int:id_furniture_type>/delete", methods=["POST"])
@auth_required()
def delete_furniture_type(id_furniture_type: int):
    """
    Alterna el estado (Activo/Inactivo) de un tipo de mueble existente.
    """
    try:
        FurnitureTypeService.toggle_status(id_furniture_type)
        flash("Estado del tipo de mueble actualizado exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("furniture_type.list_furniture_type"))


@furniture_type_bp.route("/bulk-deactivate", methods=["POST"])
@auth_required()
def bulk_deactivate():
    """
    Desactiva múltiples tipos de mueble a la vez.
    """
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("furniture_type.list_furniture_type"))

    try:
        ids = [
            int(id_str.strip())
            for id_str in ids_str.split(",")
            if id_str.strip().isdigit()
        ]
        count = FurnitureTypeService.bulk_deactivate(ids)
        flash(f"{count} tipo(s) de mueble desactivado(s) exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("furniture_type.list_furniture_type"))


@furniture_type_bp.route("/bulk-activate", methods=["POST"])
@auth_required()
def bulk_activate():
    """
    Activa múltiples tipos de mueble a la vez.
    """
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("furniture_type.list_furniture_type"))

    try:
        ids = [
            int(id_str.strip())
            for id_str in ids_str.split(",")
            if id_str.strip().isdigit()
        ]
        count = FurnitureTypeService.bulk_activate(ids)
        flash(f"{count} tipo(s) de mueble activado(s) exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("furniture_type.list_furniture_type"))


@furniture_type_bp.route("/bulk-export", methods=["POST"])
@auth_required()
def bulk_export():
    """Exportar múltiples tipos de mueble seleccionados a CSV."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("furniture_type.list_furniture_type"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    furniture_types = FurnitureTypeService.get_by_ids(ids)
    if not furniture_types:
        flash("No se encontraron registros para exportar", "error")
        return redirect(url_for("furniture_type.list_furniture_type"))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Titulo", "Estado"])
    for f in furniture_types:
        writer.writerow([f.id, f.title, "Activo" if f.status else "Inactivo"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="tipos_mueble_{timestamp}.csv"'
    )
    return response
