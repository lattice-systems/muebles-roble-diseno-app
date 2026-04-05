"""
Rutas/Endpoints para el módulo de roles.
"""

from flask import flash, redirect, render_template, request, url_for
from flask_security import auth_required

from . import roles_bp
from .forms import RoleForm
from .services import RoleService
from app.exceptions import ConflictError, NotFoundError, ValidationError


@roles_bp.route("/", methods=["GET"])
@auth_required()
def list_roles():
    """
    Muestra la lista de roles del catálogo.

    Returns:
        HTML: Página con la lista de roles
    """
    roles = RoleService.get_all()
    return render_template("roles/list.html", roles=roles)


@roles_bp.route("/create", methods=["GET", "POST"])
@auth_required()
def create_role():
    """
    Muestra el formulario y crea un nuevo rol en el catálogo.

    GET: Renderiza el formulario de creación.
    POST: Valida el formulario, crea el rol y redirige.

    Returns:
        GET - HTML: Página con el formulario de creación de rol
        POST - Redirect: Redirige al formulario con mensaje flash
    """
    form = RoleForm()

    if form.validate_on_submit():
        data = {"name": form.name.data}
        try:
            RoleService.create(data)
            flash("Rol creado exitosamente", "success")
            return redirect(url_for("roles.create_role"))
        except ConflictError as e:
            flash(e.message, "error")

    return render_template("roles/create.html", form=form)


@roles_bp.route("/<int:id_role>/edit", methods=["GET", "POST"])
@auth_required()
def edit_role(id_role: int):
    """
    Muestra el formulario pre-poblado y actualiza un rol existente.

    GET: Renderiza el formulario con los datos actuales del rol.
    POST: Valida el formulario, actualiza el rol y redirige (Patrón PRG).

    Returns:
        GET - HTML: Página con el formulario de edición de rol.
        POST - Redirect: Redirige a la lista o al formulario con mensaje flash.
    """
    try:
        role = RoleService.get_by_id(id_role)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("roles.list_roles"))

    form = RoleForm()

    if form.validate_on_submit():
        data = {"name": form.name.data}
        try:
            RoleService.update(id_role, data)
            flash("Rol actualizado exitosamente", "success")
            return redirect(url_for("roles.list_roles"))
        except (ConflictError, ValidationError) as e:
            flash(e.message, "error")

    elif request.method == "GET":
        # Pre-poblar el formulario en peticiones GET
        form.name.data = role.name

    return render_template("roles/edit.html", form=form, role=role)


@roles_bp.route("/<int:id_role>/delete", methods=["POST"])
@auth_required()
def delete_role(id_role: int):
    """
    Ejecuta la eliminación lógica de un rol.

    POST: Marca el rol como inactivo y redirige.

    Returns:
        Redirect: Redirige a la lista de roles con un mensaje flash.
    """
    try:
        RoleService.delete(id_role)
        flash("Rol eliminado exitosamente", "success")
    except NotFoundError as e:
        flash(e.message, "error")

    # Redirección al listado (Patrón PRG)
    return redirect(url_for("roles.list_roles"))
