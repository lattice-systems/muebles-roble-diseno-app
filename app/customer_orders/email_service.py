"""Servicio de correo para eventos de las órdenes de clientes (Cancelado, Enviado, Entregado)."""

import logging
import os
import threading

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)

LOGO_FILENAME = "logo-roble-disenio.png"

def _get_logo_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "static", "src", "images", LOGO_FILENAME)

def _build_items_and_totals(order):
    order_total = float(order.total or 0)
    items = [
        {
            "name": (
                item.product.name if item.product else f"Producto #{item.product_id}"
            ),
            "sku": item.product.sku if item.product else "-",
            "quantity": item.quantity,
            "price": float(item.price),
            "subtotal": float(item.price) * int(item.quantity or 0),
        }
        for item in order.items
    ]
    products_total = sum(float(item["subtotal"]) for item in items)
    freight_cost = max(order_total - products_total, 0)
    iva_rate = 0.16
    subtotal = products_total / (1 + iva_rate) if products_total else 0
    iva = products_total - subtotal

    return items, subtotal, iva, products_total, freight_cost


def _send_customer_order_email(order, template_name: str, subject_prefix: str) -> None:
    customer = order.customer
    if not customer or not customer.email:
        logger.warning("No se envió email para orden #%s: cliente sin email.", order.id)
        return

    customer_email = customer.email
    customer_name = customer.full_name
    order_id = order.id
    order_total = float(order.total or 0)

    payment_method = (
        order.payment_method.name if order.payment_method is not None else "Sin método"
    )
    
    sale_date = order.order_date.strftime("%d/%m/%Y %H:%M") if order.order_date else "-"
    
    items, subtotal, iva, products_total, freight_cost = _build_items_and_totals(order)
    
    cancel_reason = getattr(order, 'cancelled_reason', None)
    order_source = order.source
    employee_name = order.created_by.full_name if order.created_by else None

    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                logo_cid = "company_logo"
                html_body = render_template(
                    template_name,
                    source=order_source,
                    customer_name=customer_name,
                    folio=f"{order_id:06d}",
                    sale_date=sale_date,
                    payment_method=payment_method,
                    employee_name=employee_name,
                    items=items,
                    subtotal=subtotal,
                    iva=iva,
                    products_total=products_total,
                    freight_zone=None,
                    freight_free=(freight_cost == 0),
                    freight_cost=freight_cost,
                    total=order_total,
                    cancel_reason=cancel_reason,
                    logo_cid=logo_cid,
                )

                msg = Message(
                    subject=f"{subject_prefix} #{order_id:06d} — Roble y Diseño",
                    recipients=[customer_email],
                    html=html_body,
                )

                logo_path = _get_logo_path()
                if os.path.isfile(logo_path):
                    with open(logo_path, "rb") as fp:
                        msg.attach(
                            filename=LOGO_FILENAME,
                            content_type="image/png",
                            data=fp.read(),
                            disposition="inline",
                            headers={"Content-ID": f"<{logo_cid}>"},
                        )

                mail.send(msg)
                logger.info("Email '%s' enviado a %s para orden #%s", template_name, customer_email, order_id)
            except Exception as exc:
                logger.error("Error enviando email '%s' a la orden #%s: %s", template_name, order_id, exc, exc_info=True)

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()

def send_order_cancelled_email(order) -> None:
    _send_customer_order_email(order, "utils/order_cancelled_email.html", "Orden Cancelada")

def send_order_status_email(order) -> None:
    if order.status == "enviado":
        _send_customer_order_email(order, "utils/order_shipped_email.html", "Pedido Enviado")
    elif order.status == "entregado":
        _send_customer_order_email(order, "utils/order_delivered_email.html", "Pedido Entregado")
