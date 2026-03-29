"""
Script de siembra para productos y tipos de mueble.

Uso:
    .venv\\Scripts\\activate
    python scripts/seed_products.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.furniture_type import FurnitureType
from app.models.product import Product

FURNITURE_TYPES = [
    {"title": "Silla"},
    {"title": "Mesa"},
    {"title": "Sofa"},
    {"title": "Cama"},
    {"title": "Estante"},
    {"title": "Armario"},
    {"title": "Escritorio"},
    {"title": "Comoda"},
]

PRODUCTS = [
    # Sillas
    {
        "sku": "SL-001",
        "name": "Silla Nordica Roble",
        "type": "Silla",
        "description": "Silla de comedor estilo escandinavo, madera de roble macizo.",
        "price": 1_850.00,
    },
    {
        "sku": "SL-002",
        "name": "Silla Ejecutiva Pro",
        "type": "Silla",
        "description": "Silla ergonomica de oficina con respaldo alto y apoyabrazos.",
        "price": 3_200.00,
    },
    {
        "sku": "SL-003",
        "name": "Silla Infantil",
        "type": "Silla",
        "description": "Silla de madera para ninos de 3 a 8 anos.",
        "price": 650.00,
    },
    {
        "sku": "SL-004",
        "name": "Silla Thonet Clasica",
        "type": "Silla",
        "description": "Silla bentwood de estilo vintage, acabado wengue.",
        "price": 1_200.00,
    },
    # Mesas
    {
        "sku": "MS-001",
        "name": "Mesa Comedor 6 Personas",
        "type": "Mesa",
        "description": "Mesa rectangular de pino natural, 160 x 80 cm.",
        "price": 4_500.00,
    },
    {
        "sku": "MS-002",
        "name": "Mesa de Centro Minimalista",
        "type": "Mesa",
        "description": "Mesa de sala con estructura tubular y tablero de madera clara.",
        "price": 2_100.00,
    },
    {
        "sku": "MS-003",
        "name": "Mesa Auxiliar Redonda",
        "type": "Mesa",
        "description": "Mesa auxiliar circular, 60 cm de diametro, madera de bambu.",
        "price": 980.00,
    },
    # Escritorios
    {
        "sku": "ES-001",
        "name": "Escritorio Esquinero L",
        "type": "Escritorio",
        "description": "Escritorio en L para oficina en casa, MDF blanco brillante.",
        "price": 3_750.00,
    },
    {
        "sku": "ES-002",
        "name": "Escritorio Minimalista",
        "type": "Escritorio",
        "description": "Escritorio recto con soporte para monitor, 120 x 60 cm.",
        "price": 2_400.00,
    },
    # Sofas
    {
        "sku": "SF-001",
        "name": "Sofa 3 Plazas Laguna",
        "type": "Sofa",
        "description": "Sofa tapizado en tela gris con estructura de madera de eucalipto.",
        "price": 8_900.00,
    },
    {
        "sku": "SF-002",
        "name": "Sillon Individual Relax",
        "type": "Sofa",
        "description": "Sillon de descanso con mecanismo reclinable, cuero sintetico.",
        "price": 4_200.00,
    },
    # Camas
    {
        "sku": "CB-001",
        "name": "Cama Matrimonial Arena",
        "type": "Cama",
        "description": "Base y cabecero tapizado, 150 x 190 cm, tela beige.",
        "price": 6_500.00,
    },
    {
        "sku": "CB-002",
        "name": "Cama Individual Junior",
        "type": "Cama",
        "description": "Cama individual con cajones almacenadores, 90 x 190 cm.",
        "price": 3_900.00,
    },
    {
        "sku": "CB-003",
        "name": "Cama King Avalon",
        "type": "Cama",
        "description": "Base king 200 x 200 cm, cabecero acolchado, madera de acacia.",
        "price": 11_500.00,
    },
    # Estantes / Armarios / Comodas
    {
        "sku": "LB-001",
        "name": "Librero Modular Oslo",
        "type": "Estante",
        "description": "Sistema modular de 5 niveles, pino barnizado natural.",
        "price": 3_100.00,
    },
    {
        "sku": "AR-001",
        "name": "Armario 3 Puertas Sliding",
        "type": "Armario",
        "description": "Ropero con puertas corredizas y espejo incluido, 240 cm alto.",
        "price": 9_200.00,
    },
    {
        "sku": "CD-001",
        "name": "Comoda 6 Cajones Vintage",
        "type": "Comoda",
        "description": "Comoda de madera de mango con jaladores dorados.",
        "price": 4_800.00,
    },
]


def seed_products():
    app = create_app()
    with app.app_context():

        # ── 1. Tipos de mueble ──────────────────────────────────────────
        print("\n📦 Sembrando tipos de mueble...")
        type_map: dict[str, int] = {}

        for ft_data in FURNITURE_TYPES:
            existing = FurnitureType.query.filter_by(title=ft_data["title"]).first()
            if existing:
                print(f"  ⏭️  Omitido: {existing.title} (ya existe, id={existing.id})")
                type_map[existing.title] = existing.id
            else:
                ft = FurnitureType(
                    title=ft_data["title"],
                    status=True,
                )
                db.session.add(ft)
                db.session.commit()
                type_map[ft.title] = ft.id
                print(f"  ✅ Creado: {ft.title} (id={ft.id})")

        # ── 2. Productos ────────────────────────────────────────────────
        print("\n🪑 Sembrando productos...")
        seeded = 0

        for p_data in PRODUCTS:
            existing = Product.query.filter_by(sku=p_data["sku"]).first()
            if existing:
                print(f"  ⏭️  Omitido: {p_data['sku']} – {p_data['name']}")
                continue

            furniture_type_id = type_map.get(p_data["type"])
            if not furniture_type_id:
                print(
                    f"  ❌ Sin tipo de mueble '{p_data['type']}' — se omite {p_data['sku']}"
                )
                continue

            product = Product(
                sku=p_data["sku"],
                name=p_data["name"],
                furniture_type_id=furniture_type_id,
                description=p_data["description"],
                price=p_data["price"],
                status=True,
            )
            db.session.add(product)
            db.session.commit()
            seeded += 1
            print(f"  ✅ {p_data['sku']} – {p_data['name']}  ${p_data['price']:,.2f}")

        print(f"\n✨ Siembra completa: {seeded} producto(s) insertado(s).\n")


if __name__ == "__main__":
    seed_products()
