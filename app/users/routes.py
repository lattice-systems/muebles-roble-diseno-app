from flask import flash, redirect, render_template, request, url_for
from flask_security import current_user

from app.users import users_bp
from app.exceptions import NotFoundError
from app.users.services import UserService


@users_bp.route("/", methods=["GET"])
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
