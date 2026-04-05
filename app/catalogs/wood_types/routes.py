""" "
Rutas/Endpoints para el módulo de tipos de madera.
"""

import csv
from datetime import datetime
from io import StringIO
from flask import flash, redirect, render_template, request, url_for, make_response
from flask_security import auth_required
from . import woods_types_bp
from .forms import WoodTypeForm
from .services import WoodTypeService
from app.exceptions import ConflictError


@woods_types_bp.route("/", methods=["GET"])
@auth_required()
def list_wood_types():
    """
    Muestra la lista de tipos de madera del catálogo filtrada y paginada.

    Returns:
        HTML: Página con la lista de tipos de madera
    """
    search_term = request.args.get("q", "")
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = WoodTypeService.get_all(
        search_term=search_term, status_filter=status_filter, page=page
    )
    form = WoodTypeForm()

    return render_template(
        "admin/wood_types/index.html",
        wood_types=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
    )


@woods_types_bp.route("/create", methods=["POST"])
@auth_required()
def create_wood_type():
    """
    Crea un nuevo tipo de madera y maneja el modal de creación.

    POST: Valida el formulario, crea el tipo de madera y redirige o vuelve a la lista.
    Returns:
        POST - Redirect: Redirige a la lista o re-renderiza con errores
    """
    form = WoodTypeForm()

    if form.validate_on_submit():
        # Read the status from the select (not part of WTForms)
        raw_status = request.form.get("status", "1")
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "status": bool(int(raw_status)) if raw_status.isdigit() else True,
        }
        try:
            WoodTypeService.create(data)
            flash("Tipo de madera creado exitosamente", "success")
            return redirect(url_for("woods_types.list_wood_types"))
        except ConflictError as e:
            flash(e.message, "error")

    pagination = WoodTypeService.get_all()
    return render_template(
        "admin/wood_types/index.html",
        wood_types=pagination.items,
        pagination=pagination,
        form=form,
        show_create_modal=True,
    )


@woods_types_bp.route("/<int:id_wood_type>/edit", methods=["POST"])
@auth_required()
def edit_wood_type(id_wood_type: int):
    """
    Actualiza un tipo de madera existente manejado a través de modales.

    POST: Valida el formulario, actualiza el tipo de madera y redirige o vuelve a la lista.
    Returns:
        POST - Redirect o Render HTML con errores
    """
    form = WoodTypeForm()

    if form.validate_on_submit():
        raw_status = request.form.get("status", "1")
        data = {
            "name": form.name.data,
            "description": form.description.data,
            "status": bool(int(raw_status)) if raw_status.isdigit() else True,
        }
        try:
            WoodTypeService.update(id_wood_type, data)
            flash("Tipo de madera actualizado exitosamente", "success")
            return redirect(url_for("woods_types.list_wood_types"))
        except ConflictError as e:
            flash(e.message, "error")

    pagination = WoodTypeService.get_all()
    blank_form = WoodTypeForm()
    return render_template(
        "admin/wood_types/index.html",
        wood_types=pagination.items,
        pagination=pagination,
        form=blank_form,
        edit_form=form,
        show_edit_modal=id_wood_type,
    )


@woods_types_bp.route("/<int:id_wood_type>/delete", methods=["POST"])
@auth_required()
def delete_wood_type(id_wood_type: int):
    """
    Alterna el estado (Activo/Inactivo) de un tipo de madera existente.

    POST: Cambia el estatus y redirige.

    Returns:
        POST - Redirect: Redirige a la lista con mensaje flash
    """
    try:
        WoodTypeService.toggle_status(id_wood_type)
        flash("Estado del tipo de madera actualizado exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("woods_types.list_wood_types"))


@woods_types_bp.route("/bulk-deactivate", methods=["POST"])
@auth_required()
def bulk_deactivate():
    """
    Desactiva múltiples tipos de madera a la vez.

    POST: Recibe IDs separados por coma y los desactiva.

    Returns:
        POST - Redirect: Redirige a la lista con mensaje flash
    """
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("woods_types.list_wood_types"))

    try:
        ids = [
            int(id_str.strip())
            for id_str in ids_str.split(",")
            if id_str.strip().isdigit()
        ]
        count = WoodTypeService.bulk_deactivate(ids)
        flash(f"{count} tipo(s) de madera desactivado(s) exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("woods_types.list_wood_types"))


@woods_types_bp.route("/bulk-activate", methods=["POST"])
@auth_required()
def bulk_activate():
    """
    Activa múltiples tipos de madera a la vez.

    POST: Recibe IDs separados por coma y los activa.

    Returns:
        POST - Redirect: Redirige a la lista con mensaje flash
    """
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("woods_types.list_wood_types"))

    try:
        ids = [
            int(id_str.strip())
            for id_str in ids_str.split(",")
            if id_str.strip().isdigit()
        ]
        count = WoodTypeService.bulk_activate(ids)
        flash(f"{count} tipo(s) de madera activado(s) exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("woods_types.list_wood_types"))


@woods_types_bp.route("/bulk-export", methods=["POST"])
@auth_required()
def bulk_export():
    """Exportar múltiples tipos de madera seleccionados a CSV."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron registros", "error")
        return redirect(url_for("woods_types.list_wood_types"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    wood_types = WoodTypeService.get_by_ids(ids)
    if not wood_types:
        flash("No se encontraron registros para exportar", "error")
        return redirect(url_for("woods_types.list_wood_types"))

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Estado", "Descripcion"])
    for w in wood_types:
        writer.writerow(
            [w.id, w.name, "Activo" if w.status else "Inactivo", w.description or ""]
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="tipos_madera_{timestamp}.csv"'
    )
    return response
