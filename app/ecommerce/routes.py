"""Rutas iniciales para e-commerce."""

from decimal import Decimal
from urllib.parse import urlparse

from flask import abort, jsonify, redirect, render_template, request, session, url_for

from . import ecommerce_bp
from .services import EcommerceService


def _resolve_redirect_target(default_endpoint: str = "ecommerce.cart"):
    """Obtiene un destino de redirección seguro dentro del mismo sitio."""
    requested_target = (request.form.get("next") or request.referrer or "").strip()
    if not requested_target:
        return redirect(url_for(default_endpoint))

    parsed_url = urlparse(requested_target)
    if parsed_url.scheme and parsed_url.netloc and parsed_url.netloc != request.host:
        return redirect(url_for(default_endpoint))

    if parsed_url.scheme in {"http", "https"}:
        safe_target = parsed_url.path or "/"
        if parsed_url.query:
            safe_target = f"{safe_target}?{parsed_url.query}"
        return redirect(safe_target)

    if requested_target.startswith("/"):
        return redirect(requested_target)

    return redirect(url_for(default_endpoint))


def _build_checkout_form_data(raw_data: dict | None = None) -> dict:
    data = {
        "first_name": "",
        "last_name": "",
        "company": "",
        "country": "MX",
        "street": "",
        "city": "",
        "state": "",
        "zip_code": "",
        "phone": "",
        "email": "",
        "neighborhood": "",
        "exterior_number": "",
        "interior_number": "",
        "notes": "",
        "delivery_mode": "shipping",
        "payment_method_id": "",
    }
    if raw_data:
        for key in data:
            if key in raw_data and raw_data.get(key) is not None:
                data[key] = str(raw_data.get(key))
    return data


def _render_checkout(
    *,
    form_data: dict | None = None,
    error_message: str | None = None,
    status_code: int = 200,
):
    cart_data = EcommerceService.get_cart()
    payment_methods = EcommerceService.get_ecommerce_payment_methods()
    normalized_form_data = _build_checkout_form_data(form_data)

    if (
        not normalized_form_data.get("payment_method_id")
        and payment_methods
        and cart_data.get("total_items", 0) > 0
    ):
        normalized_form_data["payment_method_id"] = str(payment_methods[0].id)

    quote_error = None
    if normalized_form_data["delivery_mode"] == "shipping" and (
        not normalized_form_data.get("city", "").strip()
        or not normalized_form_data.get("state", "").strip()
    ):
        quote = {
            "cost": 0.0,
            "zone": None,
            "free": False,
            "delivery_days": 0,
            "reason": "Completa ciudad y estado para cotizar el envio.",
            "total_with_freight": float(cart_data.get("total", 0)),
        }
    else:
        try:
            quote = EcommerceService.quote_freight(
                delivery_mode=normalized_form_data["delivery_mode"],
                city=normalized_form_data.get("city", ""),
                state=normalized_form_data.get("state", ""),
                cart_total=Decimal(str(cart_data.get("total", 0))),
            )
        except Exception:
            quote = {
                "cost": 0.0,
                "zone": None,
                "free": False,
                "delivery_days": 0,
                "reason": "",
                "total_with_freight": float(cart_data.get("total", 0)),
            }
            quote_error = "No fue posible cotizar el envio en este momento."

    return (
        render_template(
            "store/checkout.html",
            cart=cart_data,
            payment_methods=payment_methods,
            form_data=normalized_form_data,
            checkout_error=error_message,
            quote_error=quote_error,
            freight_quote=quote,
            active_section="",
        ),
        status_code,
    )


@ecommerce_bp.context_processor
def inject_cart():
    """Hace que el carrito esté disponible globalmente para el cart_sidebar en todas las páginas."""
    return dict(cart=EcommerceService.get_cart())


@ecommerce_bp.route("/")
def home():
    """Página principal del e-commerce."""
    products = EcommerceService.get_featured_products()
    all_categories = EcommerceService.get_product_categories()
    featured_categories = EcommerceService.get_featured_categories()
    return render_template(
        "store/home.html",
        products=products,
        categories=all_categories,
        featured_categories=featured_categories,
        active_section="home",
    )


@ecommerce_bp.route("/categories")
def categories():
    """Página de categorías completas (Tienda)."""
    all_categories = EcommerceService.get_product_categories()
    all_products = EcommerceService.get_all_products()
    return render_template(
        "store/categories.html",
        categories=all_categories,
        products=all_products,
        active_section="categories",
    )


@ecommerce_bp.route("/search")
def search():
    """Búsqueda global en catálogos y productos."""
    search_term = request.args.get("q", "", type=str)
    search_results = EcommerceService.search_catalogs_and_products(
        search_term=search_term,
        product_limit=12,
    )
    return render_template(
        "store/search.html",
        search_term=search_results["search_term"],
        categories=search_results["categories"],
        products=search_results["products"],
        categories_total=search_results["categories_total"],
        products_total=search_results["products_total"],
        total_results=search_results["total_results"],
        active_section="",
    )


@ecommerce_bp.route("/products")
def products():
    """Página de listado de productos con búsqueda y filtros."""
    search_term = request.args.get("q", "", type=str)
    type_slug = request.args.get("type", "", type=str)
    sort_by = request.args.get("sort", "default", type=str)
    limit = request.args.get("limit", 16, type=int) or 16
    page = request.args.get("page", 1, type=int) or 1

    filtered_catalog = EcommerceService.get_filtered_products(
        search_term=search_term,
        type_slug=type_slug,
        sort_by=sort_by,
        limit=limit,
        page=page,
    )
    all_categories = EcommerceService.get_product_categories()

    return render_template(
        "store/products.html",
        products=filtered_catalog["products"],
        categories=all_categories,
        total_products=filtered_catalog["total_products"],
        filtered_total=filtered_catalog["filtered_total"],
        filters={
            "q": filtered_catalog["search_term"],
            "type": filtered_catalog["type_slug"],
            "sort": filtered_catalog["sort_by"],
            "limit": filtered_catalog["limit"],
            "page": filtered_catalog["page"],
        },
        pagination={
            "page": filtered_catalog["page"],
            "total_pages": filtered_catalog["total_pages"],
            "has_prev": filtered_catalog["has_prev"],
            "has_next": filtered_catalog["has_next"],
            "prev_page": filtered_catalog["prev_page"],
            "next_page": filtered_catalog["next_page"],
            "start_item": filtered_catalog["start_item"],
            "end_item": filtered_catalog["end_item"],
            "page_numbers": filtered_catalog["page_numbers"],
        },
        limit_options=[8, 16, 24, 32, 48],
        active_section="products",
    )


@ecommerce_bp.route("/product/<int:product_id>")
def product(product_id: int):
    """Página de detalle de producto."""
    product_data = EcommerceService.get_product_by_id(product_id)
    if not product_data:
        featured_products = EcommerceService.get_featured_products()
        product_data = featured_products[0] if featured_products else None
    if not product_data:
        abort(404)

    related_products = [
        item
        for item in EcommerceService.get_featured_products()
        if item.get("id") != product_data.get("id")
    ][:4]

    return render_template(
        "store/product.html",
        product=product_data,
        related_products=related_products,
        active_section="products",  # Maintain "Productos" highlighted in navbar
    )


@ecommerce_bp.route("/cart")
def cart():
    """Página del carrito de compras."""
    cart_data = EcommerceService.get_cart()
    return render_template("store/cart.html", cart=cart_data, active_section="")


@ecommerce_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id: int):
    """Agrega un producto al carrito de sesión."""
    quantity = request.form.get("quantity", 1, type=int) or 1
    EcommerceService.add_product_to_cart(product_id=product_id, quantity=quantity)
    return _resolve_redirect_target(default_endpoint="ecommerce.products")


@ecommerce_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart_item(product_id: int):
    """Actualiza la cantidad de un producto dentro del carrito."""
    quantity = request.form.get("quantity", 1, type=int)
    safe_quantity = quantity if quantity is not None else 1
    EcommerceService.update_product_quantity(
        product_id=product_id, quantity=safe_quantity
    )
    return _resolve_redirect_target(default_endpoint="ecommerce.cart")


@ecommerce_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id: int):
    """Elimina un producto del carrito de sesión."""
    EcommerceService.remove_product_from_cart(product_id=product_id)
    return _resolve_redirect_target(default_endpoint="ecommerce.cart")


@ecommerce_bp.route("/cart/clear", methods=["POST"])
def clear_cart():
    """Vacía todo el carrito de sesión."""
    EcommerceService.clear_cart()
    return _resolve_redirect_target(default_endpoint="ecommerce.cart")


@ecommerce_bp.route("/checkout", methods=["GET"])
def checkout():
    """Página de finalizar compra."""
    return _render_checkout()


@ecommerce_bp.route("/checkout", methods=["POST"])
def process_checkout():
    """Procesa el checkout de e-commerce y genera la orden."""
    payload = request.form.to_dict()
    try:
        result = EcommerceService.checkout_from_form(payload)
        order = result["order"]

        from .email_service import send_ecommerce_order_email

        send_ecommerce_order_email(
            order=order,
            freight=result["freight"],
            products_total=result["products_total"],
        )

        EcommerceService.clear_cart()
        session["ecommerce_last_order_id"] = order.id
        session.modified = True
        return redirect(url_for("ecommerce.checkout_success", order_id=order.id))
    except ValueError as exc:
        return _render_checkout(
            form_data=payload,
            error_message=str(exc),
            status_code=400,
        )
    except Exception:
        import traceback

        traceback.print_exc()
        return _render_checkout(
            form_data=payload,
            error_message=(
                "Ocurrio un error procesando tu pedido. "
                "Intenta nuevamente en unos minutos."
            ),
            status_code=500,
        )


@ecommerce_bp.route("/checkout/success", methods=["GET"])
def checkout_success():
    """Muestra el resumen final del ultimo pedido de ecommerce."""
    order_id_raw = request.args.get("order_id") or session.get(
        "ecommerce_last_order_id"
    )
    if not order_id_raw:
        return redirect(url_for("ecommerce.checkout"))

    try:
        order_id = int(order_id_raw)
    except (TypeError, ValueError):
        return redirect(url_for("ecommerce.checkout"))

    from app.customer_orders.services import CustomerOrderService

    order = CustomerOrderService.get_order_by_id(order_id)
    if order.source != "ecommerce":
        abort(404)

    products_total = sum(float(item.price) * int(item.quantity) for item in order.items)
    order_total = float(order.total or 0)
    freight_cost = max(order_total - products_total, 0.0)

    # Desglose IVA (alineado con POS)
    iva_rate = 0.16
    subtotal_sin_iva = (
        round(products_total / (1 + iva_rate), 2) if products_total else 0.0
    )
    iva = round(products_total - subtotal_sin_iva, 2)

    # Datos de envío del cliente
    customer = order.customer
    shipping_address = None
    if customer and customer.requires_freight:
        parts = [
            customer.street or "",
            f"#{ customer.exterior_number}" if customer.exterior_number else "",
            f"Int. {customer.interior_number}" if customer.interior_number else "",
        ]
        line1 = " ".join(p for p in parts if p).strip()
        line2_parts = [
            customer.neighborhood or "",
            f"C.P. {customer.zip_code}" if customer.zip_code else "",
        ]
        line2 = ", ".join(p for p in line2_parts if p)
        line3_parts = [
            customer.city or "",
            customer.state or "",
        ]
        line3 = ", ".join(p for p in line3_parts if p)
        shipping_address = {"line1": line1, "line2": line2, "line3": line3}

    return render_template(
        "store/checkout_success.html",
        order=order,
        products_total=products_total,
        subtotal_sin_iva=subtotal_sin_iva,
        iva=iva,
        freight_cost=freight_cost,
        shipping_address=shipping_address,
        active_section="",
    )


@ecommerce_bp.route("/api/cp/<string:cp>", methods=["GET"])
def lookup_cp(cp: str):
    """Consulta CP usando COPOMEX para autocompletar direccion."""
    from app.sales.copomex_service import CopomexService

    result = CopomexService.lookup_cp(cp)
    if result is None:
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Codigo postal no encontrado o invalido.",
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


@ecommerce_bp.route("/freight/quote", methods=["POST"])
def freight_quote():
    """Cotiza flete de checkout para envio/recoleccion."""
    data = request.get_json(silent=True) or request.form.to_dict()
    delivery_mode = (data.get("delivery_mode") or "shipping").strip().lower()
    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()

    if delivery_mode not in {"shipping", "pickup"}:
        return jsonify({"error": "Tipo de entrega invalido."}), 400

    if delivery_mode == "shipping" and (not city or not state):
        return (
            jsonify({"error": "Ciudad y estado son obligatorios para cotizar envio."}),
            400,
        )

    cart_total_raw = data.get("cart_total")
    try:
        cart_total = Decimal(str(cart_total_raw))
    except Exception:
        cart_total = Decimal(str(EcommerceService.get_cart().get("total", 0)))

    quote = EcommerceService.quote_freight(
        delivery_mode=delivery_mode,
        city=city,
        state=state,
        cart_total=cart_total,
    )
    return jsonify(quote)


@ecommerce_bp.route("/contact")
def contact():
    """Página de contacto."""
    return render_template("store/contact.html", active_section="contact")


@ecommerce_bp.route("/about")
def about():
    """Página sobre nosotros."""
    return render_template("store/about.html", active_section="about")
