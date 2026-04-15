"""Servicio de correo para confirmación de pedidos ecommerce."""

from __future__ import annotations

import logging

from flask import render_template

from app.security_mail import LOGO_CID, send_branded_email

logger = logging.getLogger(__name__)


def send_ecommerce_order_email(order, freight: dict, products_total: float) -> None:
    """Envía confirmación por correo para una orden de ecommerce."""
    customer = order.customer
    if not customer or not customer.email:
        logger.warning(
            "No se envió email para orden ecommerce #%s: cliente sin email.",
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
        order.payment_method.name if order.payment_method is not None else "Sin método"
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

    # Envío síncrono para evitar pérdidas silenciosas cuando los hilos
    # de fondo no se ejecutan de forma confiable en el servidor.
    try:
        logo_cid = LOGO_CID
        html_body = render_template(
            "utils/order_confirmation_email.html",
            source="ecommerce",
            customer_name=customer_name,
            folio=f"{order_id:06d}",
            order_date=order_date,
            estimated_delivery=estimated_delivery,
            payment_method=payment_method,
            employee_name=None,
            items=items,
            subtotal=subtotal,
            iva=iva,
            products_total=products_total,
            freight_zone=freight.get("zone"),
            freight_free=bool(freight.get("free", False)),
            freight_cost=freight_cost,
            total=order_total,
            amount_received=None,
            change=None,
            logo_cid=logo_cid,
        )

        send_branded_email(
            template="order_confirmation_ecommerce",
            subject=f"Confirmación de pedido #{order_id:06d} — Roble y Diseño",
            recipient=customer_email,
            html=html_body,
            body=(
                f"Hola {customer_name},\n\n"
                f"Recibimos tu pedido #{order_id:06d}.\n"
                f"Total: ${order_total:,.2f}.\n\n"
                "Roble y Diseño"
            ),
        )
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
