"""
Rutas/Endpoints para el módulo de ventas POS.
"""

from decimal import Decimal

from flask import jsonify, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user
from sqlalchemy.orm import selectinload

from . import sales_bp
from .services import SaleService
from .copomex_service import CopomexService
from .freight_config import calculate_freight
from .email_service import send_purchase_email
from app.models.customer import Customer


def _resolve_primary_product_image(product) -> str | None:
    """Devuelve la imagen principal del producto según sort_order."""
    images = sorted(
        product.images or [],
        key=lambda image: (
            getattr(image, "sort_order", None) is None,
            getattr(image, "sort_order", 0),
            getattr(image, "id", 0),
        ),
    )
    for image in images:
        image_url = (getattr(image, "image_url", "") or "").strip()
        if image_url:
            return image_url
    return None


@sales_bp.route("/pos", methods=["GET"])
@auth_required()
def pos():
    """
    Vista principal del POS.
    La venta se mantiene entera en sesión.
    """
    search_term = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)

    # Recuperar cliente de la sesión
    pos_customer = None
    pos_customer_id = session.get("pos_customer_id")
    if pos_customer_id:
        pos_customer = Customer.query.get(pos_customer_id)
        if not pos_customer:
            session.pop("pos_customer_id", None)

    pagination = SaleService.get_products(search_term=search_term, page=page)

    return render_template(
        "sales/pos.html",
        pos_customer=pos_customer,
        products=pagination.items,
        pagination=pagination,
        search_term=search_term,
    )


@sales_bp.route("/pos/open", methods=["POST"])
@auth_required()
def open_sale():
    """
    Asigna o quita el cliente del POS.

    Solo guarda el customer_id en la sesión, NO crea registros en BD.
    Si ya hay una venta activa con items, también actualiza su customer_id.
    """
    customer_id_raw = request.form.get("customer_id")
    customer_id = (
        int(customer_id_raw) if customer_id_raw and customer_id_raw.isdigit() else None
    )

    # Guardar/quitar cliente en sesión
    if customer_id:
        session["pos_customer_id"] = customer_id
    else:
        session.pop("pos_customer_id", None)

    return redirect(url_for("sales.pos"))


@sales_bp.route("/pos/customers", methods=["GET"])
@auth_required()
def search_customers():
    """
    Endpoint JSON para búsqueda predictiva de clientes.

    Query params:
        q: Término de búsqueda (mínimo 2 caracteres).

    Returns:
        JSON: Lista de clientes con id, full_name y email.
    """
    q = request.args.get("q", "").strip()
    customers = SaleService.search_customers(q)
    return jsonify(customers)


@sales_bp.route("/pos/customers", methods=["POST"])
@auth_required()
def create_customer():
    """
    Crea un nuevo cliente desde el POS.
    """
    try:
        data = request.get_json()
        if (
            not data
            or not data.get("first_name")
            or not data.get("last_name")
            or not data.get("email")
            or not data.get("phone")
        ):
            return (
                jsonify(
                    {"error": "Nombre, apellidos, correo y teléfono son obligatorios."}
                ),
                400,
            )

        customer = SaleService.create_customer(data)
        return jsonify({"success": True, "customer": customer.to_dict()})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


@sales_bp.route("/pos/customers/<int:customer_id>", methods=["GET"])
@auth_required()
def get_customer(customer_id):
    """Retorna los datos del cliente en JSON para los modales de ver/editar."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Cliente no encontrado."}), 404
    return jsonify(customer.to_dict())


@sales_bp.route("/pos/customers/<int:customer_id>", methods=["PUT"])
@auth_required()
def update_customer_data(customer_id):
    """Actualiza los datos de un cliente existente."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Cliente no encontrado."}), 404

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos."}), 400

        customer.first_name = data.get("first_name", customer.first_name)
        customer.last_name = data.get("last_name", customer.last_name)
        customer.email = data.get("email", customer.email)
        customer.phone = data.get("phone", customer.phone)
        customer.requires_freight = data.get("requires_freight", False)
        customer.zip_code = data.get("zip_code", customer.zip_code)
        customer.state = data.get("state", customer.state)
        customer.city = data.get("city", customer.city)
        customer.street = data.get("street", customer.street)
        customer.neighborhood = data.get("neighborhood", customer.neighborhood)
        customer.exterior_number = data.get("exterior_number", customer.exterior_number)
        customer.interior_number = data.get("interior_number", customer.interior_number)

        from app.extensions import db

        db.session.commit()
        return jsonify({"success": True, "customer": customer.to_dict()})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error al actualizar: {str(e)}"}), 500


@sales_bp.route("/pos/cart", methods=["GET"])
@auth_required()
def get_cart():
    cart = session.get("pos_cart", [])

    if cart:
        from app.models.product import Product

        product_ids = []
        for item in cart:
            raw_product_id = item.get("product_id")
            if isinstance(raw_product_id, int):
                product_ids.append(raw_product_id)
            elif isinstance(raw_product_id, str) and raw_product_id.isdigit():
                product_ids.append(int(raw_product_id))

        if product_ids:
            products = (
                Product.query.options(selectinload(Product.images))
                .filter(Product.id.in_(set(product_ids)))
                .all()
            )
            image_by_product_id = {
                product.id: _resolve_primary_product_image(product)
                for product in products
            }

            updated = False
            for item in cart:
                product_id = item.get("product_id")
                if isinstance(product_id, str) and product_id.isdigit():
                    product_id = int(product_id)

                image_url = image_by_product_id.get(product_id)
                if image_url and item.get("image_url") != image_url:
                    item["image_url"] = image_url
                    updated = True

            if updated:
                session["pos_cart"] = cart

    subtotal = sum(item.get("subtotal", 0) for item in cart)

    # Calcular flete según el cliente en sesión
    customer_id = session.get("pos_customer_id")
    customer = Customer.query.get(customer_id) if customer_id else None
    freight = calculate_freight(customer, Decimal(str(subtotal)))

    total_with_freight = subtotal + freight["cost"]
    return jsonify(
        {
            "items": cart,
            "total": total_with_freight,
            "products_total": subtotal,
            **freight,
        }
    )


@sales_bp.route("/pos/items", methods=["POST"])
@auth_required()
def add_item():
    try:
        data = request.get_json()
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity", 1))

        from app.models.product import Product
        from app.models.product_inventory import ProductInventory

        product = (
            Product.query.options(selectinload(Product.images))
            .filter_by(id=product_id, status=True)
            .first()
        )
        if not product:
            return jsonify({"error": "El producto no existe o está inactivo."}), 400

        primary_image = _resolve_primary_product_image(product)

        inventory = ProductInventory.query.filter_by(product_id=product.id).first()
        available_stock = inventory.stock if inventory else 0

        cart = session.get("pos_cart", [])
        existing = next((i for i in cart if i["product_id"] == product_id), None)
        current_qty = existing["quantity"] if existing else 0
        new_qty = current_qty + quantity

        if new_qty > available_stock:
            return (
                jsonify(
                    {
                        "error": f"Stock insuficiente para '{product.name}'. Disponible: {available_stock}, solicitado: {new_qty}."
                    }
                ),
                400,
            )

        if existing:
            existing["quantity"] = new_qty
            existing["subtotal"] = float(product.price) * new_qty
            if primary_image and existing.get("image_url") != primary_image:
                existing["image_url"] = primary_image
        else:
            cart.append(
                {
                    "id": product_id,
                    "product_id": product_id,
                    "name": product.name,
                    "sku": product.sku,
                    "image_url": primary_image,
                    "price": float(product.price),
                    "quantity": quantity,
                    "subtotal": float(product.price) * quantity,
                }
            )

        session["pos_cart"] = cart
        return jsonify({"success": True})
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


@sales_bp.route("/pos/items/<int:item_id>", methods=["PUT"])
@auth_required()
def update_item(item_id):
    try:
        data = request.get_json()
        quantity = int(data.get("quantity", 0))
        if quantity < 1:
            return jsonify({"error": "La cantidad debe ser mayor a 0."}), 400

        cart = session.get("pos_cart", [])
        existing = next((i for i in cart if i["id"] == item_id), None)
        if not existing:
            return jsonify({"error": "Detalle no encontrado en el carrito."}), 404

        from app.models.product_inventory import ProductInventory

        inventory = ProductInventory.query.filter_by(product_id=item_id).first()
        available_stock = inventory.stock if inventory else 0

        if quantity > available_stock:
            return (
                jsonify(
                    {
                        "error": f"Stock insuficiente. Disponible: {available_stock}, solicitado: {quantity}."
                    }
                ),
                400,
            )

        existing["quantity"] = quantity
        existing["subtotal"] = existing["price"] * quantity
        session.modified = True
        return jsonify({"success": True})
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


@sales_bp.route("/pos/items/<int:item_id>", methods=["DELETE"])
@auth_required()
def remove_item(item_id):
    cart = session.get("pos_cart", [])
    cart = [i for i in cart if i["id"] != item_id]
    session["pos_cart"] = cart
    return jsonify({"success": True})


@sales_bp.route("/pos/cart/clear", methods=["DELETE"])
@auth_required()
def clear_cart():
    session.pop("pos_cart", None)
    return jsonify({"success": True})


@sales_bp.route("/pos/checkout", methods=["POST"])
@auth_required()
def checkout():
    cart = session.get("pos_cart", [])
    if not cart:
        return jsonify({"error": "El carrito está vacio no hay nada que cobrar."}), 400

    customer_id = session.get("pos_customer_id")
    if not customer_id:
        return (
            jsonify({"error": "Debes asignar un cliente antes de confirmar el cobro."}),
            400,
        )

    try:
        data = request.get_json()
        amount_given = float(data.get("amount_given", 0))
        payment_method_id = int(data.get("payment_method_id", 0))

        if payment_method_id <= 0:
            return jsonify({"error": "Método de pago inválido"}), 400

        customer = Customer.query.get(customer_id)
        cart_subtotal = sum(Decimal(str(item["subtotal"])) for item in cart)
        freight = calculate_freight(customer, cart_subtotal)
        freight_cost = Decimal(str(freight["cost"]))

        result = SaleService.checkout_session_sale(
            employee_id=current_user.id,
            customer_id=customer_id,
            cart_items=cart,
            amount_given=amount_given,
            payment_method_id=payment_method_id,
            freight_cost=freight_cost,
        )

        # Enviar email de confirmación
        from app.models.payment import Payment as PaymentModel
        from app.models.sale import Sale as SaleModel
        from app.models.sale_item import SaleItem as SaleItemModel

        completed_sale = SaleModel.query.get(result["sale_id"])
        completed_items = SaleItemModel.query.filter_by(sale_id=result["sale_id"]).all()
        completed_payment = PaymentModel.query.filter_by(
            id_sale=result["sale_id"]
        ).first()
        send_purchase_email(completed_sale, completed_items, completed_payment, freight)

        # Auto-crear Orden de Cliente (HU-14)
        from app.customer_orders.services import CustomerOrderService

        CustomerOrderService.create_from_pos(
            customer_id=customer_id,
            cart_items=cart,
            payment_method_id=payment_method_id,
            employee_id=current_user.id,
            total=Decimal(str(result["total"])),
            sale_id=result["sale_id"],
        )

        session.pop("pos_cart", None)
        session.pop("pos_customer_id", None)

        return jsonify(result)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor. Revisa el log."}), 500


@sales_bp.route("/pos/payment-methods", methods=["GET"])
@auth_required()
def get_payment_methods():
    methods = SaleService.get_payment_methods()
    return jsonify([{"id": m.id, "name": m.name} for m in methods])


@sales_bp.route("/api/cp/<string:cp>", methods=["GET"])
@auth_required()
def lookup_cp(cp):
    """
    Proxy hacia COPOMEX con caché en memoria.

    Retorna estado, municipio y colonias para un CP de 5 dígitos.
    Solo consume 1 crédito por CP único (los siguientes son cache hits).
    """
    result = CopomexService.lookup_cp(cp)

    if result is None:
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Código postal no encontrado o inválido.",
                }
            ),
            404,
        )

    return jsonify(
        {
            "error": False,
            "estado": result["estado"],
            "municipio": result["municipio"],
            "colonias": result["colonias"],
        }
    )


@sales_bp.route("/<int:sale_id>/ticket", methods=["GET"])
@auth_required()
def ticket(sale_id):
    """Renderiza el ticket térmico para imprimir."""
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem
    from app.models.payment import Payment

    sale = Sale.query.get_or_404(sale_id)
    items = SaleItem.query.filter_by(sale_id=sale.id).all()
    payment = Payment.query.filter_by(id_sale=sale.id).first()

    # Calcular flete para mostrar en ticket
    products_total = sum(i.price * i.quantity for i in items)
    freight = calculate_freight(sale.customer, products_total)

    return render_template(
        "sales/ticket.html",
        sale=sale,
        items=items,
        payment=payment,
        freight=freight,
        products_total=float(products_total),
    )
