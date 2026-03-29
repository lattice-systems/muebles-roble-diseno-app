"""
Rutas/Endpoints para el módulo de ventas POS.
"""

from flask import jsonify, redirect, render_template, request, session, url_for
from flask_security import auth_required, current_user

from . import sales_bp
from .services import SaleService, SaleItemService
from .copomex_service import CopomexService
from app.exceptions import NotFoundError
from app.models.customer import Customer


@sales_bp.route("/pos", methods=["GET"])
@auth_required()
def pos():
    """
    Vista principal del POS.

    La venta se crea bajo demanda (al agregar el primer producto).
    El cliente se almacena en la sesión, no crea registros en BD.
    """
    search_term = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)

    # Recuperar venta activa (si existe)
    sale = None
    sale_id = session.get("active_sale_id")
    if sale_id:
        try:
            sale = SaleService.get_active_sale(sale_id)
        except NotFoundError:
            session.pop("active_sale_id", None)

    # Recuperar cliente de la sesión (independiente de la venta)
    pos_customer = None
    pos_customer_id = session.get("pos_customer_id")
    if pos_customer_id:
        pos_customer = Customer.query.get(pos_customer_id)
        if not pos_customer:
            session.pop("pos_customer_id", None)

    pagination = SaleService.get_products(search_term=search_term, page=page)

    return render_template(
        "sales/pos.html",
        sale=sale,
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

    # Si ya existe una venta activa con items, actualizar su customer_id
    sale_id = session.get("active_sale_id")
    if sale_id:
        try:
            sale = SaleService.get_active_sale(sale_id)
            SaleService.update_customer(sale, customer_id)
        except NotFoundError:
            session.pop("active_sale_id", None)

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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


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

    # Crear venta bajo demanda si aún no existe
    if not sale_id:
        customer_id = session.get("pos_customer_id")
        sale = SaleService.open_sale(
            employee_id=current_user.id,
            customer_id=customer_id,
        )
        session["active_sale_id"] = sale.id
        sale_id = sale.id

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
        # Validar que la venta tenga cliente asignado
        sale = SaleService.get_active_sale(sale_id)
        if not sale.id_customer:
            return jsonify({"error": "Debes asignar un cliente antes de confirmar el cobro."}), 400

        data = request.get_json()
        amount_given = float(data.get("amount_given", 0))
        payment_method_id = int(data.get("payment_method_id", 0))

        if payment_method_id <= 0:
            return jsonify({"error": "Método de pago inválido"}), 400

        result = SaleService.checkout_sale(sale_id, amount_given, payment_method_id)

        # Limpiar carrito y cliente de sesión
        session.pop("active_sale_id", None)
        session.pop("pos_customer_id", None)

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


@sales_bp.route("/sales/<int:sale_id>/ticket", methods=["GET"])
@auth_required()
def ticket(sale_id):
    """Renderiza el ticket térmico para imprimir."""
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem
    from app.models.payment import Payment

    sale = Sale.query.get_or_404(sale_id)
    items = SaleItem.query.filter_by(sale_id=sale.id).all()
    payment = Payment.query.filter_by(id_sale=sale.id).first()
    
    return render_template("sales/ticket.html", sale=sale, items=items, payment=payment)

