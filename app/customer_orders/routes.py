"""
Rutas/Endpoints para el módulo de Órdenes de Cliente (HU-14).
"""

from datetime import datetime

from flask import jsonify, render_template, request, url_for
from flask_security import auth_required, current_user

from app.exceptions import AppException

from . import customer_orders_bp
from .email_service import (
    send_order_cancelled_email,
    send_order_delivered_email,
    send_order_shipped_email,
)
from .services import CustomerOrderService

# --------------------------------------------------------------------------- #
#  Vistas HTML                                                                 #
# --------------------------------------------------------------------------- #


@customer_orders_bp.route("/", methods=["GET"])
@auth_required()
def index():
    """Vista principal: lista de órdenes con filtros."""
    customer_q = request.args.get("customer", "").strip()
    status = request.args.get("status", "").strip()
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    page = request.args.get("page", 1, type=int)

    date_from = None
    date_to = None
    try:
        if date_from_str:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        if date_to_str:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    pagination = CustomerOrderService.get_orders(
        customer_q=customer_q,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=10,
    )

    from app.models.order import Order

    return render_template(
        "customer_orders/index.html",
        orders=pagination.items,
        pagination=pagination,
        filters={
            "customer": customer_q,
            "status": status,
            "date_from": date_from_str,
            "date_to": date_to_str,
        },
        valid_statuses=Order.VALID_STATUSES,
    )


@customer_orders_bp.route("/<int:order_id>", methods=["GET"])
@auth_required()
def detail(order_id: int):
    """Vista de detalle e historial de una orden."""
    order = CustomerOrderService.get_order_by_id(order_id)
    history = CustomerOrderService.get_order_history(order_id)
    from app.models.order import Order

    return render_template(
        "customer_orders/detail.html",
        order=order,
        history=history,
        valid_statuses=Order.VALID_STATUSES,
    )


# --------------------------------------------------------------------------- #
#  API JSON                                                                    #
# --------------------------------------------------------------------------- #


@customer_orders_bp.route("/", methods=["POST"])
@auth_required()
def create():
    """Crea una nueva orden de cliente (JSON)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos."}), 400

        customer_id = data.get("customer_id")
        items = data.get("items", [])
        estimated_delivery_date_str = data.get("estimated_delivery_date", "")
        payment_method_id = data.get("payment_method_id") or None
        notes = data.get("notes", "")

        if not customer_id:
            return jsonify({"error": "El cliente es obligatorio."}), 400

        if not estimated_delivery_date_str:
            return (
                jsonify({"error": "La fecha estimada de entrega es obligatoria."}),
                400,
            )

        estimated_delivery_date = datetime.strptime(
            estimated_delivery_date_str, "%Y-%m-%d"
        ).date()

        order = CustomerOrderService.create_order(
            customer_id=int(customer_id),
            items=items,
            estimated_delivery_date=estimated_delivery_date,
            payment_method_id=int(payment_method_id) if payment_method_id else None,
            notes=notes,
            source="manual",
            created_by_id=current_user.id,
        )
        return jsonify(
            {
                "success": True,
                "order_id": order.id,
                "redirect_url": url_for("customer_orders.detail", order_id=order.id),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@customer_orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
@auth_required()
def cancel(order_id: int):
    """Cancela una orden (solo si está en estado 'pendiente')."""
    try:
        data = request.get_json()
        reason = (data or {}).get("reason", "").strip()
        if not reason:
            return jsonify({"error": "El motivo de cancelación es obligatorio."}), 400

        order = CustomerOrderService.cancel_order(
            order_id=order_id,
            user_id=current_user.id,
            reason=reason,
        )

        # Enviar correo de cancelación al cliente
        send_order_cancelled_email(order)

        return jsonify({"success": True, "status": order.status})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@customer_orders_bp.route("/<int:order_id>/send-to-production", methods=["POST"])
@auth_required()
def send_to_production(order_id: int):
    """Genera órdenes de producción a partir de la orden de cliente."""
    try:
        prod_orders = CustomerOrderService.send_to_production(
            order_id=order_id,
            user_id=current_user.id,
        )
        return jsonify(
            {
                "success": True,
                "production_orders_created": len(prod_orders),
                "production_order_ids": [p.id for p in prod_orders],
            }
        )
    except (ValueError, AppException) as e:
        message = e.message if isinstance(e, AppException) else str(e)
        status_code = e.status_code if isinstance(e, AppException) else 400
        return jsonify({"error": message}), status_code
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@customer_orders_bp.route("/<int:order_id>/status", methods=["PUT"])
@auth_required()
def update_status(order_id: int):
    """Actualiza el estado de una orden."""
    try:
        data = request.get_json()
        new_status = (data or {}).get("status", "")
        if not new_status:
            return jsonify({"error": "El estado es obligatorio."}), 400

        order = CustomerOrderService.update_status(
            order_id=order_id,
            new_status=new_status,
            user_id=current_user.id,
        )

        # Enviar correo de notificación al cliente
        if order.status == "enviado":
            send_order_shipped_email(order)
        elif order.status == "entregado":
            send_order_delivered_email(order)

        return jsonify({"success": True, "status": order.status})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@customer_orders_bp.route("/customers", methods=["GET"])
@auth_required()
def search_customers():
    """Búsqueda predictiva de clientes (JSON)."""
    q = request.args.get("q", "").strip()
    return jsonify(CustomerOrderService.search_customers(q))


@customer_orders_bp.route("/products-api", methods=["GET"])
@auth_required()
def search_products_api():
    """Búsqueda de productos para el selector (JSON)."""
    q = request.args.get("q", "").strip()
    pagination = CustomerOrderService.get_products(search_term=q, per_page=20)
    result = []
    for p in pagination.items:
        stock = p.inventory_records[0].stock if p.inventory_records else 0
        result.append(
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "price": float(p.price),
                "stock": stock,
            }
        )
    return jsonify(result)
