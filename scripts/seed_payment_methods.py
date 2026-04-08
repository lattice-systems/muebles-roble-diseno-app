"""Seed idempotente de metodos de pago coherentes para POS y ecommerce.

Uso:
    venv/bin/python scripts/seed_payment_methods.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.payment_method import PaymentMethod

PAYMENT_METHODS = [
    {
        "name": "Efectivo",
        "type": "efectivo",
        "description": "Pago en efectivo para punto de venta fisico.",
        "available_pos": True,
        "available_ecommerce": False,
        "status": True,
    },
    {
        "name": "Transferencia bancaria",
        "type": "transferencia",
        "description": "Transferencia SPEI con confirmacion administrativa.",
        "available_pos": True,
        "available_ecommerce": True,
        "status": True,
    },
    {
        "name": "Tarjeta debito o credito",
        "type": "tarjeta",
        "description": "Cobro con terminal bancaria para ventas en tienda.",
        "available_pos": True,
        "available_ecommerce": False,
        "status": True,
    },
    {
        "name": "Pasarela online",
        "type": "pasarela_online",
        "description": "Pago en linea con proveedor de pasarela.",
        "available_pos": False,
        "available_ecommerce": True,
        "status": True,
    },
]


def seed_payment_methods() -> None:
    app = create_app()
    with app.app_context():
        created = 0
        updated = 0

        existing_by_name = {
            method.name.strip().lower(): method
            for method in PaymentMethod.query.order_by(PaymentMethod.id.asc()).all()
        }

        for payload in PAYMENT_METHODS:
            key = payload["name"].strip().lower()
            method = existing_by_name.get(key)

            if method is None:
                db.session.add(PaymentMethod(**payload))
                created += 1
                continue

            changed = False
            for field in (
                "type",
                "description",
                "available_pos",
                "available_ecommerce",
                "status",
            ):
                new_value = payload[field]
                if getattr(method, field) != new_value:
                    setattr(method, field, new_value)
                    changed = True

            if changed:
                updated += 1

        db.session.commit()

        active_pos = PaymentMethod.query.filter_by(
            status=True, available_pos=True
        ).count()
        active_ecommerce = PaymentMethod.query.filter_by(
            status=True,
            available_ecommerce=True,
        ).count()

        print("\nSeed de metodos de pago ejecutado correctamente.")
        print(f"- Metodos creados: {created}")
        print(f"- Metodos actualizados: {updated}")
        print(f"- Metodos activos en POS: {active_pos}")
        print(f"- Metodos activos en ecommerce: {active_ecommerce}\n")


if __name__ == "__main__":
    seed_payment_methods()
