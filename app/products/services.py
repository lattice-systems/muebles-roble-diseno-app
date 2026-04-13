from app import db
from app.models import Product, ProductColor, ProductInventory


def get_all_products():
    return Product.query.order_by(Product.id.desc()).all()


def get_product_by_id(product_id):
    return Product.query.get_or_404(product_id)


def sku_exists(sku, exclude_product_id=None):
    query = Product.query.filter(Product.sku == sku)

    if exclude_product_id:
        query = query.filter(Product.id != exclude_product_id)

    return db.session.query(query.exists()).scalar()


def create_product(form):
    if sku_exists(form.sku.data):
        raise ValueError("El SKU ya existe.")

    product = Product(
        sku=(form.sku.data or "").strip(),
        name=(form.name.data or "").strip(),
        furniture_type_id=form.furniture_type_id.data,
        description=(form.description.data or "").strip(),
        specifications=(form.specifications.data or "").strip(),
        price=form.price.data,
        is_special_request=bool(form.is_special_request.data),
        status=form.status.data,
    )

    db.session.add(product)
    db.session.flush()

    if form.color_id.data and form.color_id.data != 0:
        db.session.add(ProductColor(product_id=product.id, color_id=form.color_id.data))

    stock_value = form.stock.data if form.stock.data is not None else 0
    db.session.add(ProductInventory(product_id=product.id, stock=stock_value))

    db.session.flush()
    return product


def update_product(product, form):
    if sku_exists(form.sku.data, exclude_product_id=product.id):
        raise ValueError("El SKU ya existe.")

    product.sku = form.sku.data.strip()
    product.name = form.name.data.strip()
    product.furniture_type_id = form.furniture_type_id.data
    product.description = (form.description.data or "").strip()
    product.specifications = (form.specifications.data or "").strip()
    product.price = form.price.data
    product.is_special_request = bool(form.is_special_request.data)
    product.status = form.status.data

    current_relations = ProductColor.query.filter_by(product_id=product.id).all()

    for relation in current_relations:
        db.session.delete(relation)

    if form.color_id.data and form.color_id.data != 0:
        db.session.add(ProductColor(product_id=product.id, color_id=form.color_id.data))

    inventory = ProductInventory.query.filter_by(product_id=product.id).first()
    if inventory:
        inventory.stock = form.stock.data if form.stock.data is not None else 0
    else:
        db.session.add(
            ProductInventory(
                product_id=product.id,
                stock=form.stock.data if form.stock.data is not None else 0,
            )
        )

    db.session.flush()
    return product


def toggle_product_status(product):
    product.status = not product.status
    db.session.commit()
    return product
