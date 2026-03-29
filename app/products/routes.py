from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models import Product, FurnitureType, Color, ProductInventory, ProductImage
from . import products_bp
from .forms import ProductForm
from .services import (
    get_product_by_id,
    create_product,
    update_product,
    toggle_product_status,
)


def save_product_images(product, files):
    upload_folder = os.path.join(current_app.root_path, "static/uploads/products")

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            image = ProductImage(
                product_id=product.id, image_path=f"uploads/products/{filename}"
            )
            db.session.add(image)


@products_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    search_term = request.args.get("q", "", type=str).strip()
    status_filter = request.args.get("status", "all", type=str)

    query = Product.query

    if search_term:
        query = query.filter(
            Product.name.ilike(f"%{search_term}%")
            | Product.sku.ilike(f"%{search_term}%")
        )

    if status_filter == "active":
        query = query.filter(Product.status)
    elif status_filter == "inactive":
        query = query.filter(~Product.status)

    query = query.order_by(Product.id.desc())

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    products = pagination.items

    return render_template(
        "admin/products/index.html",
        products=products,
        pagination=pagination,
        search_term=search_term,
        status_filter=status_filter,
    )


@products_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = ProductForm()

    # cargar selects SIEMPRE antes de validar
    form.furniture_type_id.choices = [
        (f.id, f.name)
        for f in FurnitureType.query.order_by(FurnitureType.name.asc()).all()
    ]
    form.color_id.choices = [(0, "Seleccionar color")] + [
        (c.id, c.name) for c in Color.query.order_by(Color.name.asc()).all()
    ]

    if form.validate_on_submit():
        try:
            files = request.files.getlist("images")
            files = [f for f in files if f and f.filename]

            if len(files) > 4:
                flash("Máximo 4 imágenes por producto", "danger")
                return render_template("admin/products/create.html", form=form)

            product = create_product(form)

            save_product_images(product, files)

            db.session.commit()

            flash("Producto creado correctamente.", "success")
            return redirect(url_for("products.index"))

        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            print(e)
            flash("Ocurrió un error al crear el producto.", "danger")

    return render_template("admin/products/create.html", form=form)


@products_bp.route("/<int:product_id>")
@login_required
def details(product_id):
    product = get_product_by_id(product_id)
    inventory = ProductInventory.query.filter_by(product_id=product.id).first()
    return render_template(
        "admin/products/details.html", product=product, inventory=inventory
    )


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit(product_id):
    product = get_product_by_id(product_id)
    form = ProductForm(obj=product)
    files = request.files.getlist("images")
    files = [f for f in files if f and f.filename]

    current_images = len(product.images)

    if current_images + len(files) > 4:
        flash("Máximo 4 imágenes por producto", "danger")
        return render_template("admin/products/edit.html", form=form, product=product)

    update_product(product, form)

    save_product_images(product, files)

    db.session.commit()

    form.furniture_type_id.choices = [
        (f.id, f.name)
        for f in FurnitureType.query.order_by(FurnitureType.name.asc()).all()
    ]
    form.color_id.choices = [(0, "Seleccionar color")] + [
        (c.id, c.name) for c in Color.query.order_by(Color.name.asc()).all()
    ]

    if request.method == "GET":
        first_color = product.colors[0].color_id if product.colors else 0
        form.color_id.data = first_color
        inventory = ProductInventory.query.filter_by(product_id=product.id).first()
        form.stock.data = inventory.stock if inventory else 0

    if form.validate_on_submit():
        try:
            update_product(product, form)
            flash("Producto actualizado correctamente.", "success")
            return redirect(url_for("products.index"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Ocurrió un error al actualizar el producto.", "danger")

    return render_template("admin/products/edit.html", form=form, product=product)


@products_bp.route("/<int:product_id>/toggle-status", methods=["POST"])
@login_required
def change_status(product_id):
    product = get_product_by_id(product_id)
    toggle_product_status(product)

    flash("Estado del producto actualizado.", "success")
    return redirect(url_for("products.index"))


@products_bp.route("/bulk-action", methods=["POST"])
@login_required
def bulk_action_products():
    import csv
    from io import StringIO
    from flask import make_response

    action = request.form.get("action", "").strip()
    selected_ids_raw = request.form.get("selected_ids", "").strip()

    search_term = request.form.get("q", "", type=str)
    status_filter = request.form.get("status", "all", type=str)
    page = request.form.get("page", 1, type=int)

    if not selected_ids_raw:
        flash("No se seleccionó ningún producto.", "warning")
        return redirect(
            url_for("products.index", page=page, q=search_term, status=status_filter)
        )

    try:
        selected_ids = [
            int(product_id.strip())
            for product_id in selected_ids_raw.split(",")
            if product_id.strip().isdigit()
        ]
    except ValueError:
        flash("Los productos seleccionados no son válidos.", "danger")
        return redirect(
            url_for("products.index", page=page, q=search_term, status=status_filter)
        )

    if not selected_ids:
        flash("No se seleccionó ningún producto válido.", "warning")
        return redirect(
            url_for("products.index", page=page, q=search_term, status=status_filter)
        )

    products = Product.query.filter(Product.id.in_(selected_ids)).all()

    if not products:
        flash("No se encontraron productos para aplicar la acción.", "warning")
        return redirect(
            url_for("products.index", page=page, q=search_term, status=status_filter)
        )

    if action == "activate":
        for product in products:
            product.status = True
        db.session.commit()
        flash("Los productos seleccionados fueron activados correctamente.", "success")

    elif action == "deactivate":
        for product in products:
            product.status = False
        db.session.commit()
        flash(
            "Los productos seleccionados fueron desactivados correctamente.", "success"
        )
    elif action == "export":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "SKU",
                "Nombre",
                "Tipo de mueble",
                "Precio",
                "Stock",
                "Estado",
                "Color",
            ]
        )

        for product in products:
            furniture_type = (
                product.furniture_type.name if product.furniture_type else ""
            )
            stock = (
                product.inventory_records[0].stock if product.inventory_records else 0
            )
            status = "Activo" if product.status else "Inactivo"
            color = product.colors[0].color.name if product.colors else ""

            writer.writerow(
                [
                    product.id,
                    product.sku,
                    product.name,
                    furniture_type,
                    product.price,
                    stock,
                    status,
                    color,
                ]
            )

        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = (
            "attachment; filename=productos_seleccionados.csv"
        )
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        return response

    else:
        flash("La acción solicitada no es válida.", "danger")

    return redirect(
        url_for("products.index", page=page, q=search_term, status=status_filter)
    )
