"""
Rutas/Endpoints para el módulo de tipo de mueble.
"""

from flask import flash, redirect, render_template, url_for

from . import furniture_type_bp
from .forms import FurnitureTypeForm
from .services import FurnitureTypeService
from app.exceptions import ConflictError


@furniture_type_bp.route("/", methods=["GET"])
def list_furniture_type():
    """
    Muestra la lista de tipo de mueble del catálogo.

    Returns:
        HTML: Página con la lista de tipo de mueble
    """
    furniture_type = FurnitureTypeService.get_all()
    return render_template("furniture_type/list.html", furniture_type=furniture_type)


@furniture_type_bp.route("/create", methods=["GET", "POST"])
def create_furniture_type():
    """
    Muestra el formulario y crea un nuevo tipo de mueble en el catálogo.

    GET: Renderiza el formulario de creación.
    POST: Valida el formulario, crea el tipo de mueble y redirige.

    Returns:
        GET - HTML: Página con el formulario de creación de tipo de mueble
        POST - Redirect: Redirige al formulario con mensaje flash
    """
    form = FurnitureTypeForm()

    if form.validate_on_submit():
        data = {"name": form.name.data}
        try:
            FurnitureTypeService.create(data)
            flash("Tipo de mueble creado exitosamente", "success")
            return redirect(url_for("furniture_type.create_furniture_type"))
        except ConflictError as e:
            flash(e.message, "error")

    return render_template("furniture_type/create.html", form=form)
