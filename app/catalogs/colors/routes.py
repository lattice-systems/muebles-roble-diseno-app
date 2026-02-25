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
    Muestra la lista de colores del catálogo.

    Returns:
        HTML: Página con la lista de colores
    """
    colors = ColorService.get_all()
    return render_template("colors/list.html", colors=colors)


@colors_bp.route("/create", methods=["GET", "POST"])
def create_color():
    """
    Muestra el formulario y crea un nuevo color en el catálogo.

    GET: Renderiza el formulario de creación.
    POST: Valida el formulario, crea el color y redirige.

    Returns:
        GET - HTML: Página con el formulario de creación de color
        POST - Redirect: Redirige al formulario con mensaje flash
    """
    form = ColorForm()

    if form.validate_on_submit():
        data = {"name": form.name.data}
        try:
            ColorService.create(data)
            flash("Color creado exitosamente", "success")
            return redirect(url_for("colors.create_color"))
        except ConflictError as e:
            flash(e.message, "error")

    return render_template("colors/create.html", form=form)


@colors_bp.route("/<int:id_color>/edit", methods=["GET", "POST"])
def edit_color(id_color: int):
    """
    Muestra el formulario pre-poblado y actualiza un color existente.

    GET: Renderiza el formulario con los datos actuales del color.
    POST: Valida el formulario, actualiza el color y redirige (Patrón PRG).

    Returns:
        GET - HTML: Página con el formulario de edición de color.
        POST - Redirect: Redirige al formulario con mensaje flash
    """
    try:
        color = ColorService.get_by_id(id_color)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("colors.list_colors"))

    form = ColorForm()

    if form.validate_on_submit():
        data = {"name": form.name.data}
        try:
            ColorService.update(id_color, data)
            flash("Color actualizado exitosamente", "success")
            return redirect(url_for("colors.list_colors"))
        except (ConflictError, ValidationError) as e:
            flash(e.message, "error")

    elif request.method == "GET":
        # Pre-poblar el formulario en peticiones GET
        form.name.data = color.name

    return render_template("colors/edit.html", form=form, color=color)


@colors_bp.route("/<int:id_color>/delete", methods=["POST"])
def delete_color(id_color: int):
    """
    Ejecuta la eliminación logica de un color.

    POST: Marca el color como inactivo y redirige

    Returns:
        Redirect: Redirige a la lista de colors con mensaje flash

    Raises:
        NotFoundError: Si no se encuentra un color con el ID
    """
    try:
        ColorService.delete(id_color)
        flash("Color eliminado exitosamente", "success")
    except NotFoundError as e:
        flash(e.message, "error")

    return redirect(url_for("colors.list_colors"))
