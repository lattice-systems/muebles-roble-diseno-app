"""
Servicio de correo para notificaciones de órdenes de cliente.

Envía emails de notificación al cliente cuando su pedido es
enviado (estado 'enviado'), entregado (estado 'entregado')
o cancelado (estado 'cancelado').
Utiliza la misma arquitectura de hilos que el POS y ecommerce.
"""

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
    """Retorna la ruta absoluta al logo de la empresa."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "static", "src", "images", LOGO_FILENAME)


def _extract_order_data(order) -> dict:
    """
    Extrae TODOS los datos del ORM en el hilo principal
    para evitar problemas de conexión MySQL entre hilos.
    """
    customer = order.customer
    items_data = [
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

    # Dirección de envío (si el cliente tiene flete)
    shipping_address = None
    if customer and customer.requires_freight:
        parts = []
        if customer.street:
            addr = customer.street
            if customer.exterior_number:
                addr += f" #{customer.exterior_number}"
            if customer.interior_number:
                addr += f" Int. {customer.interior_number}"
            parts.append(addr)
        if customer.neighborhood:
            parts.append(f"Col. {customer.neighborhood}")
        city_state = []
        if customer.city:
            city_state.append(customer.city)
        if customer.state:
            city_state.append(customer.state)
        if city_state:
            parts.append(", ".join(city_state))
        if customer.zip_code:
            parts.append(f"C.P. {customer.zip_code}")
        shipping_address = ", ".join(parts) if parts else None

    return {
        "customer_email": customer.email if customer else None,
        "customer_name": customer.full_name if customer else "Cliente",
        "order_id": order.id,
        "folio": f"{order.id:04d}",
        "order_date": (
            order.order_date.strftime("%d/%m/%Y %H:%M") if order.order_date else "N/A"
        ),
        "estimated_delivery": (
            order.estimated_delivery_date.strftime("%d/%m/%Y")
            if order.estimated_delivery_date
            else "Por confirmar"
        ),
        "total": float(order.total or 0),
        "items": items_data,
        "shipping_address": shipping_address,
        "has_freight": bool(customer and customer.requires_freight),
        "cancelled_reason": order.cancelled_reason or None,
    }


def send_order_shipped_email(order) -> None:
    """
    Envía el correo de notificación de envío de forma asíncrona.
    Se llama cuando la orden pasa a estado 'enviado'.
    """
    data = _extract_order_data(order)

    if not data["customer_email"]:
        logger.warning(
            "No se envió email de envío para orden #%s: cliente sin email.",
            data["order_id"],
        )
        return

    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                logo_cid = "company_logo"
                html_body = render_template(
                    "utils/order_shipped_email.html",
                    **data,
                    logo_cid=logo_cid,
                )

                msg = Message(
                    subject=f"Tu pedido #{data['folio']} ha sido enviado — Roble y Diseño",
                    recipients=[data["customer_email"]],
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
                    "Email de envío enviado a %s (orden #%s)",
                    data["customer_email"],
                    data["order_id"],
                )
            except Exception as exc:
                logger.error(
                    "Error enviando email de envío (orden #%s): %s",
                    data["order_id"],
                    exc,
                    exc_info=True,
                )

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    logger.info(
        "Hilo de envío de email (shipped) iniciado para orden #%s", data["order_id"]
    )


def send_order_delivered_email(order) -> None:
    """
    Envía el correo de confirmación de entrega de forma asíncrona.
    Se llama cuando la orden pasa a estado 'entregado'.
    """
    data = _extract_order_data(order)

    if not data["customer_email"]:
        logger.warning(
            "No se envió email de entrega para orden #%s: cliente sin email.",
            data["order_id"],
        )
        return

    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                logo_cid = "company_logo"
                html_body = render_template(
                    "utils/order_delivered_email.html",
                    **data,
                    logo_cid=logo_cid,
                )

                msg = Message(
                    subject=f"Tu pedido #{data['folio']} ha sido entregado — Roble y Diseño",
                    recipients=[data["customer_email"]],
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
                    "Email de entrega enviado a %s (orden #%s)",
                    data["customer_email"],
                    data["order_id"],
                )
            except Exception as exc:
                logger.error(
                    "Error enviando email de entrega (orden #%s): %s",
                    data["order_id"],
                    exc,
                    exc_info=True,
                )

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    logger.info(
        "Hilo de envío de email (delivered) iniciado para orden #%s", data["order_id"]
    )


def send_order_cancelled_email(order) -> None:
    """
    Envía el correo de notificación de cancelación de forma asíncrona.
    Se llama cuando la orden pasa a estado 'cancelado'.
    """
    data = _extract_order_data(order)

    if not data["customer_email"]:
        logger.warning(
            "No se envió email de cancelación para orden #%s: cliente sin email.",
            data["order_id"],
        )
        return

    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                logo_cid = "company_logo"
                html_body = render_template(
                    "utils/order_cancelled_email.html",
                    **data,
                    logo_cid=logo_cid,
                )

                msg = Message(
                    subject=f"Tu pedido #{data['folio']} ha sido cancelado — Roble y Diseño",
                    recipients=[data["customer_email"]],
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
                    "Email de cancelación enviado a %s (orden #%s)",
                    data["customer_email"],
                    data["order_id"],
                )
            except Exception as exc:
                logger.error(
                    "Error enviando email de cancelación (orden #%s): %s",
                    data["order_id"],
                    exc,
                    exc_info=True,
                )

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    logger.info(
        "Hilo de envío de email (cancelled) iniciado para orden #%s", data["order_id"]
    )
