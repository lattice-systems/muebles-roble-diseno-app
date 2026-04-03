"""Servicio de correo para confirmacion de pedidos ecommerce."""

from __future__ import annotations

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


def send_ecommerce_order_email(order, freight: dict, products_total: float) -> None:
    """Envia confirmacion por correo para una orden de ecommerce."""
    customer = order.customer
    if not customer or not customer.email:
        logger.warning(
            "No se envio email para orden ecommerce #%s: cliente sin email.",
            order.id,
        )
        return

    customer_email = customer.email
    customer_name = customer.full_name
    order_id = order.id
    order_total = float(order.total or 0)
    products_total = float(products_total or 0)
    freight_cost = float(freight.get("cost", max(order_total - products_total, 0)))

    iva_rate = 0.16
    subtotal = products_total / (1 + iva_rate) if products_total else 0
    iva = products_total - subtotal

    payment_method = (
        order.payment_method.name if order.payment_method is not None else "Sin metodo"
    )
    order_date = (
        order.order_date.strftime("%d/%m/%Y %H:%M") if order.order_date else "-"
    )
    estimated_delivery = (
        order.estimated_delivery_date.strftime("%d/%m/%Y")
        if order.estimated_delivery_date
        else "Por confirmar"
    )

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

    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                logo_cid = "company_logo"
                html_body = render_template(
                    "utils/ecommerce_order_email.html",
                    customer_name=customer_name,
                    folio=f"{order_id:06d}",
                    order_date=order_date,
                    estimated_delivery=estimated_delivery,
                    payment_method=payment_method,
                    items=items,
                    subtotal=subtotal,
                    iva=iva,
                    products_total=products_total,
                    freight_zone=freight.get("zone"),
                    freight_free=bool(freight.get("free", False)),
                    freight_cost=freight_cost,
                    total=order_total,
                    logo_cid=logo_cid,
                )

                msg = Message(
                    subject=f"Confirmacion de pedido #{order_id:06d} - Roble y Diseno",
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
                logger.info(
                    "Email ecommerce enviado a %s para orden #%s",
                    customer_email,
                    order_id,
                )
            except Exception as exc:
                logger.error(
                    "Error enviando email ecommerce #%s: %s",
                    order_id,
                    exc,
                    exc_info=True,
                )

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
