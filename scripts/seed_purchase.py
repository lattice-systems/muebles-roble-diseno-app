import os
import sys
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import (
    MaterialCategory,
    PurchaseOrder,
    RawMaterial,
    Supplier,
    UnitOfMeasure,
)
from app.purchases.services import PurchaseOrderService

SUPPLIER_NAME = "Proveedor Demo Abastecimiento"
CATEGORY_NAME = "Maderas"
UNIT_NAME = "Pieza"
UNIT_ABBREVIATION = "pza"
RAW_MATERIAL_NAME = "Tablero MDF 15mm Demo"


def get_or_create_supplier() -> Supplier:
    supplier = Supplier.query.filter_by(name=SUPPLIER_NAME).first()
    if supplier:
        return supplier

    supplier = Supplier(
        name=SUPPLIER_NAME,
        phone="555-000-0000",
        email="proveedor.demo@roble.local",
        address="Sucursal demo para abastecimiento",
        status=True,
    )
    db.session.add(supplier)
    db.session.flush()
    return supplier


def get_or_create_category() -> MaterialCategory:
    category = MaterialCategory.query.filter_by(name=CATEGORY_NAME).first()
    if category:
        return category

    category = MaterialCategory(
        name=CATEGORY_NAME,
        description="Categoría base para materias primas demo",
        status="active",
    )
    db.session.add(category)
    db.session.flush()
    return category


def get_or_create_unit() -> UnitOfMeasure:
    unit = UnitOfMeasure.query.filter_by(
        name=UNIT_NAME, abbreviation=UNIT_ABBREVIATION
    ).first()
    if unit:
        return unit

    unit = UnitOfMeasure(
        name=UNIT_NAME,
        abbreviation=UNIT_ABBREVIATION,
        type="count",
        status=True,
    )
    db.session.add(unit)
    db.session.flush()
    return unit


def get_or_create_raw_material(
    supplier_id: int, category_id: int, unit_id: int
) -> RawMaterial:
    raw_material = RawMaterial.query.filter_by(name=RAW_MATERIAL_NAME).first()
    if raw_material:
        return raw_material

    raw_material = RawMaterial(
        name=RAW_MATERIAL_NAME,
        description="Materia prima de demostración para compras",
        category_id=category_id,
        unit_id=unit_id,
        waste_percentage=0,
        stock=0,
        estimated_cost=345.50,
        status="active",
        supplier_id=supplier_id,
    )
    db.session.add(raw_material)
    db.session.flush()
    return raw_material


def seed_purchase() -> PurchaseOrder:
    supplier = get_or_create_supplier()
    category = get_or_create_category()
    unit = get_or_create_unit()
    raw_material = get_or_create_raw_material(supplier.id, category.id, unit.id)

    existing = (
        PurchaseOrder.query.filter_by(supplier_id=supplier.id, status="pendiente")
        .order_by(PurchaseOrder.id.desc())
        .first()
    )
    if existing:
        return existing

    purchase = PurchaseOrderService.create(
        {
            "supplier_id": supplier.id,
            "order_date": date.today(),
            "status": "pendiente",
        },
        [
            {
                "raw_material_id": raw_material.id,
                "quantity": 12,
                "unit_price": 345.50,
            }
        ],
    )

    return purchase


def main() -> None:
    app = create_app()
    with app.app_context():
        purchase = seed_purchase()
        db.session.commit()
        print(
            f"Compra sembrada correctamente: OC-{purchase.id} | proveedor={purchase.supplier_id} | total={purchase.total}"
        )


if __name__ == "__main__":
    main()
