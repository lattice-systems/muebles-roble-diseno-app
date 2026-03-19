"""
Rutas/Endpoints para el módulo de colores.
"""

from flask import flash, redirect, render_template, request, url_for

from app.exceptions import ConflictError, NotFoundError, ValidationError

from . import colors_bp
from .forms import ColorForm
from .services import ColorService


@colors_bp.route("/", methods=["GET"])
def list_colors():
    """
    Muestra la lista de colores con búsqueda, filtro y paginación.
    """
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = ColorService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
    )

    form = ColorForm()

    return render_template(
        "colors/list.html",
        colors=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
    )


@colors_bp.route("/create", methods=["POST"])
def create_color():
    """
    Crea un nuevo color desde el modal.
    POST: Valida, crea y redirige. En error, re-renderiza con modal abierto.
    """
    form = ColorForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "hex_code": form.hex_code.data,
            "description": form.description.data,
            "status": request.form.get("status", "1"),
        }
        try:
            ColorService.create(data)
            flash("Color creado exitosamente", "success")
            return redirect(url_for("colors.list_colors"))
        except (ConflictError, ValidationError) as e:
            flash(e.message, "error")

    # Re-render list with modal open on validation error
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    pagination = ColorService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
    )
    return render_template(
        "colors/list.html",
        colors=pagination.items,
        pagination=pagination,
        form=form,
        search_term=search_term,
        status_filter=status_filter,
        show_create_modal=True,
    )


@colors_bp.route("/<int:id_color>/edit", methods=["POST"])
def edit_color(id_color: int):
    """
    Edita un color desde el modal.
    POST: Valida, actualiza y redirige. En error, re-renderiza con modal abierto.
    """
    form = ColorForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "hex_code": form.hex_code.data,
            "description": form.description.data,
            "status": request.form.get("status", "1"),
        }
        try:
            ColorService.update(id_color, data)
            flash("Color actualizado exitosamente", "success")
            return redirect(url_for("colors.list_colors"))
        except (ConflictError, ValidationError, NotFoundError) as e:
            flash(e.message, "error")

    # Re-render list with edit modal open on validation error
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    pagination = ColorService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
    )
    return render_template(
        "colors/list.html",
        colors=pagination.items,
        pagination=pagination,
        form=form,
        edit_form=form,
        search_term=search_term,
        status_filter=status_filter,
        show_edit_modal=id_color,
    )


@colors_bp.route("/<int:id_color>/delete", methods=["POST"])
def delete_color(id_color: int):
    """
    Toggle de estado de un color (desactivar/activar).
    """
    try:
        ColorService.delete(id_color)
        flash("Estado del color actualizado exitosamente", "success")
    except NotFoundError as e:
        flash(e.message, "error")

    return redirect(url_for("colors.list_colors"))


@colors_bp.route("/bulk-deactivate", methods=["POST"])
def bulk_deactivate():
    """Desactivar múltiples colores seleccionados."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron colores", "error")
        return redirect(url_for("colors.list_colors"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    count = ColorService.bulk_deactivate(ids)
    flash(f"{count} color(es) desactivado(s) exitosamente", "success")
    return redirect(url_for("colors.list_colors"))


@colors_bp.route("/bulk-activate", methods=["POST"])
def bulk_activate():
    """Activar múltiples colores seleccionados."""
    ids_str = request.form.get("ids", "")
    if not ids_str:
        flash("No se seleccionaron colores", "error")
        return redirect(url_for("colors.list_colors"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    count = ColorService.bulk_activate(ids)
    flash(f"{count} color(es) activado(s) exitosamente", "success")
    return redirect(url_for("colors.list_colors"))
