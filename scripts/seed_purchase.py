"""Seed de orden de compra base para costos de fabricacion.

Crea/actualiza una orden de compra idempotente con precios unitarios de
materia prima usados por BOM. CostService toma estos precios para calcular
material_cost en modulo de costos.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import PurchaseOrder, PurchaseOrderItem, RawMaterial, Supplier
from seed_dataset import RAW_MATERIALS

SUPPLIER_DATA = {
    "name": "Proveedor Seed Costos Fabrica",
    "phone": "555-100-2000",
    "email": "seed.costos@furniture.local",
    "address": "Centro Logistico Academico",
}
SEED_ORDER_DATE = date(2026, 4, 5)


def _to_decimal(value: str | float | int) -> Decimal:
    return Decimal(str(value))


def _seed_quantity_for_unit(unit_name: str) -> Decimal:
    if unit_name == "Metro lineal":
        return Decimal("80.000")
    if unit_name == "Litro":
        return Decimal("35.000")
    return Decimal("120.000")


def get_or_create_supplier() -> Supplier:
    supplier = Supplier.query.filter_by(name=SUPPLIER_DATA["name"]).first()
    if supplier:
        supplier.phone = SUPPLIER_DATA["phone"]
        supplier.email = SUPPLIER_DATA["email"]
        supplier.address = SUPPLIER_DATA["address"]
        supplier.status = True
        return supplier

    supplier = Supplier(
        name=SUPPLIER_DATA["name"],
        phone=SUPPLIER_DATA["phone"],
        email=SUPPLIER_DATA["email"],
        address=SUPPLIER_DATA["address"],
        status=True,
    )
    db.session.add(supplier)
    db.session.flush()
    return supplier


def _get_existing_seed_order(supplier_id: int) -> PurchaseOrder | None:
    orders = (
        PurchaseOrder.query.filter_by(
            supplier_id=supplier_id,
            order_date=SEED_ORDER_DATE,
        )
        .order_by(PurchaseOrder.id.asc())
        .all()
    )

    if not orders:
        return None

    canonical = orders[0]
    for extra in orders[1:]:
        PurchaseOrderItem.query.filter_by(purchase_order_id=extra.id).delete(
            synchronize_session=False
        )
        db.session.delete(extra)

    return canonical


def seed_purchase() -> PurchaseOrder:
    supplier = get_or_create_supplier()

    price_catalog = {
        item["name"]: _to_decimal(item["unit_price"])
        for item in RAW_MATERIALS
        if item.get("unit_price") is not None
    }
    stock_unit_catalog = {item["name"]: item["unit"] for item in RAW_MATERIALS}

    raw_materials = (
        RawMaterial.query.filter(RawMaterial.name.in_(price_catalog.keys()))
        .order_by(RawMaterial.name.asc())
        .all()
    )

    if not raw_materials:
        raise RuntimeError(
            "No hay materias primas para sembrar orden de compra. "
            "Ejecuta primero scripts/seed_raw_materials.py"
        )

    order = _get_existing_seed_order(supplier.id)
    if order is None:
        order = PurchaseOrder(
            supplier_id=supplier.id,
            order_date=SEED_ORDER_DATE,
            status="recibida",
            total=Decimal("0.00"),
        )
        db.session.add(order)
        db.session.flush()
    else:
        order.status = "recibida"
        PurchaseOrderItem.query.filter_by(purchase_order_id=order.id).delete(
            synchronize_session=False
        )

    total = Decimal("0.00")
    for raw_material in raw_materials:
        unit_name = stock_unit_catalog.get(raw_material.name, "Pieza")
        quantity = _seed_quantity_for_unit(unit_name)
        unit_price = price_catalog[raw_material.name]

        db.session.add(
            PurchaseOrderItem(
                purchase_order_id=order.id,
                raw_material_id=raw_material.id,
                quantity=quantity,
                conversion_factor=Decimal("1.000"),
                received_quantity=quantity,
                unit_price=unit_price,
            )
        )
        total += quantity * unit_price

    order.total = total
    db.session.flush()

    return order


def main() -> None:
    app = create_app()
    with app.app_context():
        purchase = seed_purchase()
        db.session.commit()
        print(
            "Compra seed de costos aplicada: "
            f"OC-{purchase.id} | proveedor={purchase.supplier_id} | total={purchase.total}"
        )


if __name__ == "__main__":
    main()
