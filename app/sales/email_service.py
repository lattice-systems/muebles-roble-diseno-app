"""
Servicio de envío de correo de confirmación de compra.

Envía un email con el detalle de la venta al cliente
utilizando Flask-Mail y las credenciales SMTP de Brevo.
"""

import logging
import os
import threading

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)

# Ruta al logo para embeber como adjunto inline
LOGO_FILENAME = "logo-roble-disenio.png"


def _get_logo_path() -> str:
    """Retorna la ruta absoluta al logo de la empresa."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "static", "src", "images", LOGO_FILENAME)


def _resolve_sender() -> str | None:
    return (
        current_app.config.get("MAIL_DEFAULT_SENDER")
        or current_app.config.get("SECURITY_EMAIL_SENDER")
        or current_app.config.get("MAIL_USERNAME")
    )


def send_purchase_email(sale, items, payment, freight: dict) -> None:
    """
    Envía el correo de confirmación de compra de forma asíncrona.

    IMPORTANTE: Toda la lectura de datos del ORM se hace en el hilo
    principal para evitar problemas de conexión MySQL entre hilos.
    El hilo secundario solo renderiza el template y envía el email.
    """
    # ── 1. Extraer TODOS los datos del ORM en el hilo principal ──────
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

    # ── 2. Capturar app context y lanzar hilo (sin acceso a DB) ──────
    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                logo_cid = "company_logo"
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

                msg = Message(
                    subject=f"Confirmación de Compra #{folio} — Roble y Diseño",
                    sender=_resolve_sender(),
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

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    logger.info("Hilo de envío de email de compra iniciado para venta #%s", sale_id)
