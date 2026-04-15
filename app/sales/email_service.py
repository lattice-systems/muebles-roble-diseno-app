"""Servicio de envío para confirmación de compra POS."""

import logging
from flask import render_template

from app.security_mail import LOGO_CID, send_branded_email

logger = logging.getLogger(__name__)


def send_purchase_email(sale, items, payment, freight: dict) -> None:
    """Envía el correo de confirmación POS usando el mail_util de seguridad."""
    customer = sale.customer
    if not customer or not customer.email:
        logger.warning(
            "No se envió email de compra para venta #%s: cliente sin email.",
            sale.id,
        )
        return

    customer_email = customer.email
    customer_name = customer.full_name
    sale_id = sale.id

    products_total = sum(float(i.price) * i.quantity for i in items)
    iva_rate = 0.16
    subtotal = products_total / (1 + iva_rate)
    iva = products_total - subtotal
    f_cost = float(freight.get("cost", 0))
    total = products_total + f_cost

    amount_received = float(payment.amount) if payment else total
    change = max(amount_received - total, 0)

    items_data = [
        {
            "name": i.product.name,
            "sku": i.product.sku,
            "quantity": i.quantity,
            "price": float(i.price),
            "subtotal": float(i.price) * i.quantity,
        }
        for i in items
    ]

    folio = f"{sale_id:06d}"
    sale_date = sale.sale_date.strftime("%d/%m/%Y %H:%M") if sale.sale_date else "N/A"
    employee_name = sale.employee.full_name if sale.employee else "N/A"
    payment_method = sale.payment_method.name if sale.payment_method else "Efectivo"

    # Envío síncrono para evitar pérdidas silenciosas en entornos
    # donde los hilos de fondo no se ejecutan de forma confiable.
    try:
        logo_cid = LOGO_CID
        html_body = render_template(
            "utils/order_confirmation_email.html",
            source="pos",
            customer_name=customer_name,
            folio=folio,
            order_date=sale_date,
            employee_name=employee_name,
            payment_method=payment_method,
            estimated_delivery=None,
            items=items_data,
            subtotal=subtotal,
            iva=iva,
            total=total,
            freight_zone=freight.get("zone"),
            freight_cost=f_cost,
            freight_free=freight.get("free", False),
            amount_received=amount_received,
            change=change,
            logo_cid=logo_cid,
        )

        send_branded_email(
            template="order_confirmation_pos",
            subject=f"Confirmación de Compra #{folio} — Roble y Diseño",
            recipient=customer_email,
            html=html_body,
            body=(
                f"Hola {customer_name},\n\n"
                f"Tu compra POS con folio #{folio} fue registrada correctamente.\n"
                f"Total: ${total:,.2f}.\n\n"
                "Roble y Diseño"
            ),
        )
        logger.info(
            "Email de compra enviado a %s (venta #%s)",
            customer_email,
            sale_id,
        )

    except Exception as exc:
        logger.error(
            "Error enviando email de compra (venta #%s): %s",
            sale_id,
            exc,
            exc_info=True,
        )
