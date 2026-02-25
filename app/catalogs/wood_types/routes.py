""""
Rutas/Endpoints para el módulo de tipos de madera.
"""
from flask import flash, redirect, render_template, url_for
from . import woods_types_bp
from .forms import WoodTypeForm 
from .services import WoodTypeService
from app.exceptions import ConflictError


@woods_types_bp.route("/", methods=["GET"])
def list_wood_types():
    """
    Muestra la lista de tipos de madera del catálogo.

    Returns:
        HTML: Página con la lista de tipos de madera
    """
    wood_types = WoodTypeService.get_all()
    return render_template("wood_types/list.html", wood_types=wood_types)

@woods_types_bp.route("/create", methods=["GET", "POST"])
def create_wood_type(): 
    """
    Muestra el formulario y crea un nuevo tipo de madera en el catálogo.

    GET: Renderiza el formulario de creación.
    POST: Valida el formulario, crea el tipo de madera y redirige.
    Returns:
        GET - HTML: Página con el formulario de creación de tipo de madera
        POST - Redirect: Redirige al formulario con mensaje flash
    """
    form = WoodTypeForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data
        }
        try:
            WoodTypeService.create(data)
            flash("Tipo de madera creado exitosamente", "success")
            return redirect(url_for("woods_types.create_wood_type"))
        except ConflictError as e:
            flash(e.message, "error")

    return render_template("wood_types/create.html", form=form)

@woods_types_bp.route("/<int:id_wood_type>/edit", methods=["GET", "POST"])
def edit_wood_type(id_wood_type: int):  
    """
    Muestra el formulario pre-poblado y actualiza un tipo de madera existente.

    GET: Renderiza el formulario con los datos actuales del tipo de madera.
    POST: Valida el formulario, actualiza el tipo de madera y redirige (Patrón PRG).

    Returns:
        GET - HTML: Página con el formulario de edición de tipo de madera.
        POST - Redirect: Redirige al formulario con mensaje flash
    """
    form = WoodTypeForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "description": form.description.data
        }
        try:
            WoodTypeService.update(id_wood_type, data)
            flash("Tipo de madera actualizado exitosamente", "success")
            return redirect(url_for("woods_types.edit_wood_type", id_wood_type=id_wood_type))
        except ConflictError as e:
            flash(e.message, "error")

    wood_type = WoodTypeService.get_by_id(id_wood_type)
    if not wood_type:
        flash("Tipo de madera no encontrado", "error")
        return redirect(url_for("woods_types.list_wood_types"))

    # Pre-popular el formulario con los datos actuales del tipo de madera
    form.name.data = wood_type.name
    form.description.data = wood_type.description

    return render_template("wood_types/edit.html", form=form, wood_type=wood_type)

@woods_types_bp.route("/<int:id_wood_type>/delete", methods=["POST"])
def delete_wood_type(id_wood_type: int):    
    """
    Elimina un tipo de madera existente.

    POST: Elimina el tipo de madera y redirige.

    Returns:
        POST - Redirect: Redirige a la lista con mensaje flash
    """
    try:
        WoodTypeService.delete(id_wood_type)
        flash("Tipo de madera eliminado exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("woods_types.list_wood_types"))