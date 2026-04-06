import os
import sys
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import MaterialCategory, RawMaterial, RawMaterialMovement, UnitOfMeasure
from seed_dataset import RAW_MATERIALS

CATEGORY_DESCRIPTIONS = {
    "Maderas": "Tableros, maderas macizas y derivados para carpinteria",
    "Herrajes": "Bisagras, correderas, tornilleria y mecanismos",
    "Acabados": "Barnices, lacas, selladores y tintes",
    "Tapiceria y rellenos": "Textiles, espumas y consumibles para tapiceria",
}

UNIT_DEFINITIONS = {
    "Pieza": ("pza", "count"),
    "Metro lineal": ("ml", "length"),
    "Litro": ("L", "volume"),
}


def _get_or_create_categories() -> dict[str, MaterialCategory]:
    categories: dict[str, MaterialCategory] = {}
    category_names = {item["category"] for item in RAW_MATERIALS}

    for name in sorted(category_names):
        category = MaterialCategory.query.filter_by(name=name).first()
        if not category:
            category = MaterialCategory(
                name=name,
                description=CATEGORY_DESCRIPTIONS.get(
                    name, "Categoria de materia prima"
                ),
                status="active",
            )
            db.session.add(category)
            db.session.flush()
        else:
            category.description = CATEGORY_DESCRIPTIONS.get(
                name,
                category.description,
            )
            category.status = "active"

        categories[name] = category
    return categories


def _get_or_create_units() -> dict[str, UnitOfMeasure]:
    units: dict[str, UnitOfMeasure] = {}
    unit_names = {item["unit"] for item in RAW_MATERIALS}

    for name in sorted(unit_names):
        abbreviation, unit_type = UNIT_DEFINITIONS[name]
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
        else:
            unit.type = unit_type
            unit.status = True

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
            waste_percentage = Decimal(str(item["waste_percentage"]))
            initial_stock = Decimal(str(item["initial_stock"]))

            if not material:
                material = RawMaterial(
                    name=item["name"],
                    description=item["description"],
                    category_id=categories[item["category"]].id,
                    unit_id=units[item["unit"]].id,
                    waste_percentage=waste_percentage,
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
                material.waste_percentage = waste_percentage
                material.status = "active"
                updated_count += 1

            if _ensure_initial_movement(material, initial_stock):
                movements_count += 1

        db.session.commit()

        print("\nSeed de materias primas ejecutado correctamente.")
        print(f"- Materias primas creadas: {created_count}")
        print(f"- Materias primas actualizadas: {updated_count}")
        print(f"- Movimientos iniciales creados: {movements_count}")


if __name__ == "__main__":
    seed_raw_materials()
