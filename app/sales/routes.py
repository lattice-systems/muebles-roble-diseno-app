"""
Rutas/Endpoints para el módulo de ventas POS.
"""

from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user

from . import sales_bp
from .services import SaleService, SaleItemService
from .copomex_service import CopomexService
from app.exceptions import NotFoundError


@sales_bp.route("/pos", methods=["GET"])
@auth_required()
def pos():
    """
    Vista principal del POS.

    Muestra la cuadrícula de productos y el panel de carrito.
    Si no existe una venta activa en sesión, auto-abre una nueva.

    Returns:
        HTML: Página del POS con productos paginados y carrito activo.
    """
    search_term = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)

    # Auto-abrir venta si no existe una activa en sesión
    sale = None
    sale_id = session.get("active_sale_id")
    if sale_id:
        try:
            sale = SaleService.get_active_sale(sale_id)
        except NotFoundError:
            session.pop("active_sale_id", None)
            sale_id = None

    if not sale:
        # Crear cabecera automáticamente al entrar al POS
        sale = SaleService.open_sale(employee_id=current_user.id)
        session["active_sale_id"] = sale.id

    pagination = SaleService.get_products(search_term=search_term, page=page)

    return render_template(
        "sales/pos.html",
        sale=sale,
        products=pagination.items,
        pagination=pagination,
        search_term=search_term,
    )


@sales_bp.route("/pos/open", methods=["POST"])
@auth_required()
def open_sale():
    """
    Abre manualmente una nueva cabecera de venta y redirige al POS.

    POST: Recibe customer_id (opcional) y crea la venta.

    Returns:
        Redirect: Redirige a la vista principal del POS.
    """
    customer_id_raw = request.form.get("customer_id")
    customer_id = (
        int(customer_id_raw) if customer_id_raw and customer_id_raw.isdigit() else None
    )

    # Cerrar venta activa anterior si la hay
    session.pop("active_sale_id", None)

    try:
        sale = SaleService.open_sale(
            employee_id=current_user.id,
            customer_id=customer_id,
        )
        session["active_sale_id"] = sale.id
    except Exception as e:
        flash(str(e), "error")

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
        if not data or not data.get("first_name") or not data.get("last_name") or not data.get("email") or not data.get("phone"):
            return jsonify({"error": "Nombre, apellidos, correo y teléfono son obligatorios."}), 400

        customer = SaleService.create_customer(data)
        return jsonify({"success": True, "customer": customer.to_dict()})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Error interno del servidor."}), 500


@sales_bp.route("/pos/cart", methods=["GET"])
@auth_required()
def get_cart():
    sale_id = session.get("active_sale_id")
    if not sale_id:
        return jsonify({"items": [], "total": 0})
    try:
        sale = SaleService.get_active_sale(sale_id)
        items = SaleItemService.get_cart_items(sale.id)
        total = sum(item.get("subtotal", 0) for item in items)
        return jsonify({"items": items, "total": total})
    except NotFoundError:
        return jsonify({"items": [], "total": 0})


@sales_bp.route("/pos/items", methods=["POST"])
@auth_required()
def add_item():
    sale_id = session.get("active_sale_id")
    if not sale_id:
        return jsonify({"error": "No hay venta activa"}), 400
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        if not product_id:
            return jsonify({"error": "Falta el ID del producto"}), 400

        quantity = data.get("quantity", 1)
        SaleItemService.add_item_to_sale(sale_id, int(product_id), int(quantity))
        return jsonify({"success": True})
    except (NotFoundError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@sales_bp.route("/pos/items/<int:item_id>", methods=["PUT"])
@auth_required()
def update_item(item_id):
    sale_id = session.get("active_sale_id")
    if not sale_id:
        return jsonify({"error": "No hay venta activa"}), 400
    try:
        data = request.get_json()
        quantity = data.get("quantity")
        if quantity is None:
            return jsonify({"error": "Falta la cantidad"}), 400

        SaleItemService.update_item_quantity(sale_id, item_id, int(quantity))
        return jsonify({"success": True})
    except (NotFoundError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@sales_bp.route("/pos/items/<int:item_id>", methods=["DELETE"])
@auth_required()
def remove_item(item_id):
    sale_id = session.get("active_sale_id")
    if not sale_id:
        return jsonify({"error": "No hay venta activa"}), 400
    try:
        SaleItemService.remove_item_from_sale(sale_id, item_id)
        return jsonify({"success": True})
    except (NotFoundError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@sales_bp.route("/pos/checkout", methods=["POST"])
@auth_required()
def checkout():
    sale_id = session.get("active_sale_id")
    if not sale_id:
        return jsonify({"error": "No hay venta activa"}), 400

    try:
        data = request.get_json()
        amount_given = float(data.get("amount_given", 0))
        payment_method_id = int(data.get("payment_method_id", 0))

        if payment_method_id <= 0:
            return jsonify({"error": "Método de pago inválido"}), 400

        result = SaleService.checkout_sale(sale_id, amount_given, payment_method_id)

        # Limpiar carrito
        session.pop("active_sale_id", None)

        return jsonify(result)
    except (NotFoundError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        return jsonify({
            "error": True,
            "message": "Código postal no encontrado o inválido.",
        }), 404

    return jsonify({
        "error": False,
        "estado": result["estado"],
        "municipio": result["municipio"],
        "colonias": result["colonias"],
    })
