import os
import sys
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import MaterialCategory, RawMaterial, RawMaterialMovement, UnitOfMeasure

CATEGORIES = [
    ("Maderas", "Tableros y maderas macizas para carpinteria"),
    ("Herrajes", "Bisagras, correderas, tornilleria y uniones"),
    ("Acabados", "Barnices, selladores, tintes y auxiliares"),
]

UNITS = [
    ("Pieza", "pza", "count"),
    ("Metro lineal", "ml", "length"),
    ("Litro", "L", "volume"),
]

RAW_MATERIALS = [
    {
        "name": "Tablero MDF 15mm",
        "description": "Panel MDF de 244x122 cm para mobiliario residencial",
        "category": "Maderas",
        "unit": "Pieza",
        "waste_percentage": Decimal("8.00"),
        "initial_stock": Decimal("35.000"),
    },
    {
        "name": "Triplay Encino 18mm",
        "description": "Triplay enchapado para frentes y tapas premium",
        "category": "Maderas",
        "unit": "Pieza",
        "waste_percentage": Decimal("10.00"),
        "initial_stock": Decimal("18.000"),
    },
    {
        "name": "Liston de Pino 2x2",
        "description": "Liston estructural cepillado",
        "category": "Maderas",
        "unit": "Metro lineal",
        "waste_percentage": Decimal("5.50"),
        "initial_stock": Decimal("240.000"),
    },
    {
        "name": "Corredera telescopica 45cm",
        "description": "Juego de correderas para cajon de extension total",
        "category": "Herrajes",
        "unit": "Pieza",
        "waste_percentage": Decimal("1.00"),
        "initial_stock": Decimal("120.000"),
    },
    {
        "name": "Bisagra cazoleta cierre suave",
        "description": "Bisagra de 35mm con cierre amortiguado",
        "category": "Herrajes",
        "unit": "Pieza",
        "waste_percentage": Decimal("1.50"),
        "initial_stock": Decimal("360.000"),
    },
    {
        "name": "Tornillo confirmat 7x50",
        "description": "Tornillo de ensamble para melamina y MDF",
        "category": "Herrajes",
        "unit": "Pieza",
        "waste_percentage": Decimal("2.00"),
        "initial_stock": Decimal("2500.000"),
    },
    {
        "name": "Barniz poliuretano mate",
        "description": "Barniz transparente para acabado de alta resistencia",
        "category": "Acabados",
        "unit": "Litro",
        "waste_percentage": Decimal("6.00"),
        "initial_stock": Decimal("32.000"),
    },
    {
        "name": "Sellador nitrocelulosa",
        "description": "Sellador base para preparacion de superficie",
        "category": "Acabados",
        "unit": "Litro",
        "waste_percentage": Decimal("7.00"),
        "initial_stock": Decimal("20.000"),
    },
]


def _get_or_create_categories() -> dict[str, MaterialCategory]:
    categories: dict[str, MaterialCategory] = {}
    for name, description in CATEGORIES:
        category = MaterialCategory.query.filter_by(name=name).first()
        if not category:
            category = MaterialCategory(
                name=name,
                description=description,
                status="active",
            )
            db.session.add(category)
            db.session.flush()
        categories[name] = category
    return categories


def _get_or_create_units() -> dict[str, UnitOfMeasure]:
    units: dict[str, UnitOfMeasure] = {}
    for name, abbreviation, unit_type in UNITS:
        unit = UnitOfMeasure.query.filter_by(
            name=name, abbreviation=abbreviation
        ).first()
        if not unit:
            unit = UnitOfMeasure(
                name=name,
                abbreviation=abbreviation,
                type=unit_type,
                status=True,
            )
            db.session.add(unit)
            db.session.flush()
        units[name] = unit
    return units


def _ensure_initial_movement(material: RawMaterial, target_stock: Decimal) -> bool:
    has_seed_reference = (
        RawMaterialMovement.query.filter_by(
            raw_material_id=material.id,
            reference="SEED-RM-INIT",
        ).first()
        is not None
    )

    if has_seed_reference:
        return False

    movement = RawMaterialMovement(
        raw_material_id=material.id,
        movement_type="ENTRADA",
        quantity=target_stock,
        reason="Carga inicial para pruebas del modulo de materias primas",
        reference="SEED-RM-INIT",
    )
    db.session.add(movement)
    material.stock = target_stock
    return True


def seed_raw_materials() -> None:
    app = create_app()
    with app.app_context():
        categories = _get_or_create_categories()
        units = _get_or_create_units()

        created_count = 0
        updated_count = 0
        movements_count = 0

        for item in RAW_MATERIALS:
            material = RawMaterial.query.filter_by(name=item["name"]).first()
            if not material:
                material = RawMaterial(
                    name=item["name"],
                    description=item["description"],
                    category_id=categories[item["category"]].id,
                    unit_id=units[item["unit"]].id,
                    waste_percentage=item["waste_percentage"],
                    stock=Decimal("0.000"),
                    status="active",
                )
                db.session.add(material)
                db.session.flush()
                created_count += 1
            else:
                material.description = item["description"]
                material.category_id = categories[item["category"]].id
                material.unit_id = units[item["unit"]].id
                material.waste_percentage = item["waste_percentage"]
                material.status = "active"
                updated_count += 1

            if _ensure_initial_movement(material, item["initial_stock"]):
                movements_count += 1

        db.session.commit()

        print("\nSeed de materias primas ejecutado correctamente.")
        print(f"- Materias primas creadas: {created_count}")
        print(f"- Materias primas actualizadas: {updated_count}")
        print(f"- Movimientos iniciales creados: {movements_count}")


if __name__ == "__main__":
    seed_raw_materials()
