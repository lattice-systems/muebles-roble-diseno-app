import csv
from datetime import datetime
from io import StringIO

from flask import flash, make_response, redirect, render_template, request, url_for
from flask_security import auth_required

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.suppliers import suppliers_bp
from app.suppliers.forms import SupplierForm
from app.suppliers.services import SupplierService


def _parse_selected_ids(raw_ids: str) -> list[int]:
    ids: list[int] = []
    for raw in (raw_ids or "").split(","):
        value = raw.strip()
        if not value or not value.isdigit():
            continue
        id_val = int(value)
        if id_val > 0 and id_val not in ids:
            ids.append(id_val)
    return ids


@suppliers_bp.route("/", methods=["GET"])
@auth_required()
def index():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    pagination = SupplierService.get_all(
        search_term=search_term or None,
        status_filter=status_filter,
        page=page,
        per_page=10,
    )

    return render_template(
        "admin/suppliers/index.html",
        suppliers=pagination.items,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
    )


@suppliers_bp.route("/create", methods=["GET", "POST"])
@auth_required()
def create_supplier():
    form = SupplierForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "phone": form.phone.data,
            "email": form.email.data,
            "address": form.address.data,
            "status": form.status.data,
        }

        try:
            SupplierService.create(data)
            flash("Proveedor creado exitosamente", "success")
            return redirect(url_for("suppliers.index"))
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    return render_template("admin/suppliers/create.html", form=form)


@suppliers_bp.route("/<int:id_supplier>/toggle-status", methods=["POST"])
@auth_required()
def toggle_status(id_supplier: int):
    search_term = request.form.get("q", "").strip()
    status_filter = request.form.get("status", "all")
    page_raw = request.form.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1

    try:
        new_status = SupplierService.toggle_status(id_supplier)
        flash(
            (
                "Proveedor activado exitosamente"
                if new_status
                else "Proveedor desactivado exitosamente"
            ),
            "success",
        )
    except NotFoundError as e:
        flash(e.message, "error")

    return redirect(
        url_for(
            "suppliers.index",
            page=page,
            q=search_term,
            status=status_filter,
        )
    )


@suppliers_bp.route("/<int:id_supplier>/edit", methods=["GET", "POST"])
@auth_required()
def edit_supplier(id_supplier: int):
    try:
        supplier = SupplierService.get_by_id(id_supplier)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("suppliers.index"))

    form = SupplierForm()

    if request.method == "GET":
        form.name.data = supplier.name
        form.phone.data = supplier.phone
        form.email.data = supplier.email
        form.address.data = supplier.address
        form.status.data = supplier.status
    elif form.validate_on_submit():
        data = {
            "name": form.name.data,
            "phone": form.phone.data,
            "email": form.email.data,
            "address": form.address.data,
            "status": form.status.data,
        }

        try:
            SupplierService.update(id_supplier, data)
            flash("Proveedor actualizado exitosamente", "success")
            return redirect(url_for("suppliers.index"))
        except (ValidationError, ConflictError) as e:
            flash(e.message, "error")

    elif request.method == "POST":
        flash("Por favor corrige los errores del formulario", "error")

    return render_template("admin/suppliers/edit.html", form=form, supplier=supplier)


@suppliers_bp.route("/<int:id_supplier>/details", methods=["GET"])
@auth_required()
def detail_supplier(id_supplier: int):
    try:
        supplier = SupplierService.get_by_id(id_supplier)
    except NotFoundError as e:
        flash(e.message, "error")
        return redirect(url_for("suppliers.index"))

    return render_template("admin/suppliers/details.html", supplier=supplier)


@suppliers_bp.route("/bulk-action", methods=["POST"])
@auth_required()
def bulk_action_suppliers():
    search_term = request.form.get("q", "").strip()
    status_filter = request.form.get("status", "all")
    page_raw = request.form.get("page", "1")
    page = int(page_raw) if page_raw.isdigit() else 1

    action = (request.form.get("action") or "").strip().lower()
    selected_ids = _parse_selected_ids(request.form.get("selected_ids", ""))

    if not selected_ids:
        flash("Selecciona al menos un proveedor", "error")
        return redirect(
            url_for(
                "suppliers.index",
                page=page,
                q=search_term,
                status=status_filter,
            )
        )

    if action == "export":
        suppliers_list = SupplierService.get_by_ids(selected_ids)
        if not suppliers_list:
            flash("No se encontraron proveedores para exportar", "error")
            return redirect(
                url_for(
                    "suppliers.index",
                    page=page,
                    q=search_term,
                    status=status_filter,
                )
            )

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Nombre",
                "Teléfono",
                "Correo Electrónico",
                "Dirección",
                "Estado",
                "Fecha de creación",
            ]
        )
        for supplier in suppliers_list:
            writer.writerow(
                [
                    supplier.id,
                    supplier.name,
                    supplier.phone or "",
                    supplier.email or "",
                    supplier.address or "",
                    "Activo" if supplier.status else "Inactivo",
                    (
                        supplier.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if supplier.created_at
                        else ""
                    ),
                ]
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=proveedores_{timestamp}.csv"
        )
        return response

    if action in {"activate", "deactivate"}:
        target_status = action == "activate"
        result = SupplierService.bulk_set_status(
            selected_ids, target_status=target_status
        )

        updated = result["updated"]
        not_found = result["not_found"]

        action_text = "activados" if target_status else "desactivados"
        flash(f"{updated} proveedor(es) {action_text}.", "success")
        if not_found:
            flash(f"{not_found} proveedor(es) no encontrado(s).", "error")

        return redirect(
            url_for(
                "suppliers.index",
                page=page,
                q=search_term,
                status=status_filter,
            )
        )

    flash("Acción masiva inválida", "error")
    return redirect(
        url_for(
            "suppliers.index",
            page=page,
            q=search_term,
            status=status_filter,
        )
    )
