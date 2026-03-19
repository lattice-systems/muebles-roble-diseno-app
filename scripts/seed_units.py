import sys
import os

# Añadir el directorio raíz al path para poder importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.unit_of_measure import UnitOfMeasure
from app.catalogs.unit_of_measures.services import UnitOfMeasureService
from app.exceptions import ConflictError


def seed_units():
    app = create_app()
    with app.app_context():
        units_to_seed = [
            {"name": "Metro", "abbreviation": "m", "type": "longitud", "active": True},
            {
                "name": "Centímetro",
                "abbreviation": "cm",
                "type": "longitud",
                "active": True,
            },
            {
                "name": "Milímetro",
                "abbreviation": "mm",
                "type": "longitud",
                "active": True,
            },
            {
                "name": "Kilómetro",
                "abbreviation": "km",
                "type": "longitud",
                "active": True,
            },
            {
                "name": "Pulgada",
                "abbreviation": "in",
                "type": "longitud",
                "active": True,
            },
            {"name": "Pie", "abbreviation": "ft", "type": "longitud", "active": True},
            {"name": "Kilogramo", "abbreviation": "kg", "type": "peso", "active": True},
            {"name": "Gramo", "abbreviation": "g", "type": "peso", "active": True},
            {"name": "Miligramo", "abbreviation": "mg", "type": "peso", "active": True},
            {"name": "Libra", "abbreviation": "lb", "type": "peso", "active": True},
            {"name": "Onza", "abbreviation": "oz", "type": "peso", "active": True},
            {"name": "Litro", "abbreviation": "L", "type": "volumen", "active": True},
            {
                "name": "Mililitro",
                "abbreviation": "mL",
                "type": "volumen",
                "active": True,
            },
            {"name": "Galón", "abbreviation": "gal", "type": "volumen", "active": True},
            {
                "name": "Onza Líquida",
                "abbreviation": "fl oz",
                "type": "volumen",
                "active": True,
            },
            {"name": "Pieza", "abbreviation": "pz", "type": "unidad", "active": True},
            {"name": "Par", "abbreviation": "par", "type": "unidad", "active": True},
            {"name": "Docena", "abbreviation": "doc", "type": "unidad", "active": True},
            {
                "name": "Paquete",
                "abbreviation": "paq",
                "type": "unidad",
                "active": True,
            },
            {"name": "Caja", "abbreviation": "caja", "type": "unidad", "active": True},
        ]

        # Evitar crear duplicados comparando con la base de datos
        existing_abbreviations = {u.abbreviation for u in UnitOfMeasure.query.all()}

        seeded_count = 0
        for unit_data in units_to_seed:
            if unit_data["abbreviation"] not in existing_abbreviations:
                try:
                    UnitOfMeasureService.create(unit_data)
                    print(f"✅ Creado: {unit_data['name']}")
                    seeded_count += 1
                except ConflictError as e:
                    print(f"❌ Error al crear {unit_data['name']}: {e}")
                except Exception as e:
                    print(f"❌ Error inesperado con {unit_data['name']}: {e}")
            else:
                print(
                    f"⏭️ Omitidido: {unit_data['name']} (abreviatura {unit_data['abbreviation']} ya existe)"
                )

        print(
            f"\nProceso finalizado. Se insertaron {seeded_count} nuevas unidades de medida."
        )


if __name__ == "__main__":
    seed_units()
