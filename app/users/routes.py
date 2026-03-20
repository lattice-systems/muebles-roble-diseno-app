import csv
from datetime import datetime
from io import StringIO

from flask import flash, make_response, redirect, render_template, request, url_for
from flask_security import current_user, login_required, auth_required, url_for_security

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.users import users_bp
from app.users.forms import UserForm, UserEditForm
from app.users.services import UserService


def _parse_selected_ids(raw_ids: str) -> list[int]:
    ids: list[int] = []
    for raw in (raw_ids or "").split(","):
        value = raw.strip()
        if not value or not value.isdigit():
            continue
        user_id = int(value)
        if user_id > 0 and user_id not in ids:
            ids.append(user_id)
    return ids


@users_bp.route("/profile", methods=["GET"])
@login_required
def profile():
	"""Muestra el perfil del usuario actual."""
	user = current_user
	has_2fa = bool(user.tf_primary_method)
	
	return render_template(
		"admin/administration/users/profile.html",
		user=user,
		has_2fa=has_2fa,
	)


@users_bp.route("/profile/setup-2fa", methods=["GET"])
@login_required
def setup_2fa():
    """Inicia el proceso de configuración de 2FA."""
    # Redirige a la ruta de Flask-Security para setup de 2FA
    return redirect(url_for_security("two_factor_setup"))


@users_bp.route("/", methods=["GET"])
@auth_required()
def index():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = UserService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
        per_page=10,
    )

    return render_template(
        "admin/administration/users/index.html",
        users=pagination.items,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
    )


@auth_required()
@users_bp.route("/create", methods=["GET", "POST"])
def create_user():
    form = UserForm()
    form.role_id.choices = UserService.get_role_choices()

    if request.method == "GET" and form.role_id.choices:
        form.role_id.data = form.role_id.choices[0][0]

    if form.validate_on_submit():
        data = {
            "full_name": form.full_name.data,
            "email": form.email.data,
            "password": form.password.data,
            "role_id": form.role_id.data,
            "status": form.status.data,
        }

        try:
            UserService.create(data)
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("users.index"))
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    if not form.role_id.choices:
        flash("No hay roles activos disponibles para asignar", "error")

    return render_template("admin/administration/users/create.html", form=form)


@auth_required()
@users_bp.route("/<int:id_user>/toggle-status", methods=["POST"])
def toggle_status(id_user: int):
    search_term = request.form.get("q", "").strip()
    status_filter = request.form.get("status", "all")
    page_raw = request.form.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1

    try:
        user = UserService.get_by_id(id_user)
        if user.status and user.id == getattr(current_user, "id", None):
            flash("No puedes desactivar tu propio usuario", "error")
            return redirect(
                url_for(
                    "users.index",
                    page=page,
                    q=search_term,
                    status=status_filter,
                )
            )

        new_status = UserService.toggle_status(id_user)
        flash(
            "Usuario activado exitosamente"
            if new_status
            else "Usuario desactivado exitosamente",
            "success",
        )
    except NotFoundError as e:
        flash(e.message, "error")

    return redirect(
        url_for(
            "users.index",
            page=page,
            q=search_term,
            status=status_filter,
        )
    )


@auth_required()
@users_bp.route("/<int:id_user>/edit", methods=["GET", "POST"])
def edit_user(id_user: int):
    try:
        user = UserService.get_by_id(id_user)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("users.index"))

    form = UserEditForm()
    form.role_id.choices = UserService.get_role_choices()

    if request.method == "GET":
        # Pre-llenar formulario con datos actuales
        form.full_name.data = user.full_name
        form.email.data = user.email
        form.role_id.data = user.role_id
        form.status.data = user.status
    elif form.validate_on_submit():
        data = {
            "full_name": form.full_name.data,
            "email": form.email.data,
            "password": form.password.data,
            "role_id": form.role_id.data,
            "status": form.status.data,
        }

        try:
            UserService.update(id_user, data)
            flash("Usuario actualizado exitosamente", "success")
            return redirect(url_for("users.index"))
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    if not form.role_id.choices:
        flash("No hay roles activos disponibles para asignar", "error")

    return render_template("admin/administration/users/edit.html", form=form, user=user)


@auth_required()
@users_bp.route("/<int:id_user>/details", methods=["GET"])
def detail_user(id_user: int):
    try:
        user = UserService.get_by_id(id_user)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("users.index"))

    return render_template("admin/administration/users/details.html", user=user)


@auth_required()
@users_bp.route("/bulk-action", methods=["POST"])
def bulk_action_users():
    search_term = request.form.get("q", "").strip()
    status_filter = request.form.get("status", "all")
    page_raw = request.form.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1

    action = (request.form.get("action") or "").strip().lower()
    selected_ids = _parse_selected_ids(request.form.get("selected_ids", ""))

    if not selected_ids:
        flash("Selecciona al menos un usuario", "error")
        return redirect(
            url_for(
                "users.index",
                page=page,
                q=search_term,
                status=status_filter,
            )
        )

    if action == "export":
        users = UserService.get_by_ids(selected_ids)
        if not users:
            flash("No se encontraron usuarios para exportar", "error")
            return redirect(
                url_for(
                    "users.index",
                    page=page,
                    q=search_term,
                    status=status_filter,
                )
            )

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Nombre", "Correo", "Rol", "Estado", "Fecha de creacion"])
        for user in users:
            writer.writerow(
                [
                    user.id,
                    user.full_name,
                    user.email,
                    user.role.name if user.role else "Sin rol",
                    "Activo" if user.status else "Inactivo",
                    user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "",
                ]
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=usuarios_seleccionados_{timestamp}.csv"
        )
        return response

    if action in {"activate", "deactivate"}:
        target_status = action == "activate"
        result = UserService.bulk_set_status(
            selected_ids,
            target_status=target_status,
            current_user_id=getattr(current_user, "id", None),
        )

        updated = result["updated"]
        skipped_self = result["skipped_self"]
        not_found = result["not_found"]

        action_text = "activados" if target_status else "desactivados"
        flash(f"{updated} usuario(s) {action_text}.", "success")
        if skipped_self:
            flash("No puedes desactivar tu propio usuario.", "error")
        if not_found:
            flash(f"{not_found} usuario(s) no encontrado(s).", "error")

        return redirect(
            url_for(
                "users.index",
                page=page,
                q=search_term,
                status=status_filter,
            )
        )

    flash("Accion masiva invalida", "error")
    return redirect(
        url_for(
            "users.index",
            page=page,
            q=search_term,
            status=status_filter,
        )
    )
