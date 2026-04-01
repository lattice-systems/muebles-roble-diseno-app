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
    {
        "title": "Salas",
        "subtitle": "Sofas, sillones individuales, sofas de dos plazas",
        "slug": "salas",
        "image_url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Comedores",
        "subtitle": "Mesas de comedor, sillas de comedor, bancos",
        "slug": "comedores",
        "image_url": "https://images.unsplash.com/photo-1617098474202-0d0d7f60a87b?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Recamaras",
        "subtitle": "Camas, cabeceras, buros",
        "slug": "recamaras",
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Closets y almacenamiento",
        "subtitle": "Closets, roperos, armarios",
        "slug": "closets-y-almacenamiento",
        "image_url": "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Escritorios y oficina",
        "subtitle": "Escritorios, sillas de oficina, estaciones de trabajo",
        "slug": "escritorios-y-oficina",
        "image_url": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Muebles para TV",
        "subtitle": "Centros de entretenimiento, bases para TV, consolas",
        "slug": "muebles-para-tv",
        "image_url": "https://images.unsplash.com/photo-1615874959474-d609969a20ed?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Mesas",
        "subtitle": "Mesas de centro, mesas laterales, mesas auxiliares",
        "slug": "mesas",
        "image_url": "https://images.unsplash.com/photo-1530018607912-eff2daa1bac4?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Estanterias y libreros",
        "subtitle": "Libreros, repisas, estantes",
        "slug": "estanterias-y-libreros",
        "image_url": "https://images.unsplash.com/photo-1594026112284-02bb6f3352fe?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Cocina",
        "subtitle": "Alacenas, islas de cocina, gabinetes",
        "slug": "cocina",
        "image_url": "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Muebles infantiles",
        "subtitle": "Camas infantiles, escritorios para ninos, organizadores",
        "slug": "muebles-infantiles",
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Muebles decorativos",
        "subtitle": "Consolas decorativas, biombos, bancos decorativos",
        "slug": "muebles-decorativos",
        "image_url": "https://images.unsplash.com/photo-1616594039964-3ff3b7f1ec30?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Muebles personalizados",
        "subtitle": "Disenos a medida, proyectos especiales, muebles bajo pedido",
        "slug": "muebles-personalizados",
        "image_url": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=1200",
    },
    {
        "title": "Muebles de jardin",
        "subtitle": "Salas de exterior, comedores de exterior, camastros y tumbonas",
        "slug": "muebles-de-jardin",
        "image_url": "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&q=80&w=1200",
    },
]
PRODUCTS = [
    # Sillas
    {
        "sku": "SL-001",
        "name": "Silla Nordica Roble",
        "type": "Comedores",
        "description": "Silla de comedor estilo escandinavo, madera de roble macizo.",
        "price": 1_850.00,
    },
    {
        "sku": "SL-002",
        "name": "Silla Ejecutiva Pro",
        "type": "Escritorios y oficina",
        "description": "Silla ergonomica de oficina con respaldo alto y apoyabrazos.",
        "price": 3_200.00,
    },
    {
        "sku": "SL-003",
        "name": "Silla Infantil",
        "type": "Muebles infantiles",
        "description": "Silla de madera para ninos de 3 a 8 anos.",
        "price": 650.00,
    },
    {
        "sku": "SL-004",
        "name": "Silla Thonet Clasica",
        "type": "Comedores",
        "description": "Silla bentwood de estilo vintage, acabado wengue.",
        "price": 1_200.00,
    },
    # Mesas
    {
        "sku": "MS-001",
        "name": "Mesa Comedor 6 Personas",
        "type": "Comedores",
        "description": "Mesa rectangular de pino natural, 160 x 80 cm.",
        "price": 4_500.00,
    },
    {
        "sku": "MS-002",
        "name": "Mesa de Centro Minimalista",
        "type": "Mesas",
        "description": "Mesa de sala con estructura tubular y tablero de madera clara.",
        "price": 2_100.00,
    },
    {
        "sku": "MS-003",
        "name": "Mesa Auxiliar Redonda",
        "type": "Mesas",
        "description": "Mesa auxiliar circular, 60 cm de diametro, madera de bambu.",
        "price": 980.00,
    },
    # Escritorios
    {
        "sku": "ES-001",
        "name": "Escritorio Esquinero L",
        "type": "Escritorios y oficina",
        "description": "Escritorio en L para oficina en casa, MDF blanco brillante.",
        "price": 3_750.00,
    },
    {
        "sku": "ES-002",
        "name": "Escritorio Minimalista",
        "type": "Escritorios y oficina",
        "description": "Escritorio recto con soporte para monitor, 120 x 60 cm.",
        "price": 2_400.00,
    },
    # Sofas
    {
        "sku": "SF-001",
        "name": "Sofa 3 Plazas Laguna",
        "type": "Salas",
        "description": "Sofa tapizado en tela gris con estructura de madera de eucalipto.",
        "price": 8_900.00,
    },
    {
        "sku": "SF-002",
        "name": "Sillon Individual Relax",
        "type": "Salas",
        "description": "Sillon de descanso con mecanismo reclinable, cuero sintetico.",
        "price": 4_200.00,
    },
    # Camas
    {
        "sku": "CB-001",
        "name": "Cama Matrimonial Arena",
        "type": "Recamaras",
        "description": "Base y cabecero tapizado, 150 x 190 cm, tela beige.",
        "price": 6_500.00,
    },
    {
        "sku": "CB-002",
        "name": "Cama Individual Junior",
        "type": "Muebles infantiles",
        "description": "Cama individual con cajones almacenadores, 90 x 190 cm.",
        "price": 3_900.00,
    },
    {
        "sku": "CB-003",
        "name": "Cama King Avalon",
        "type": "Recamaras",
        "description": "Base king 200 x 200 cm, cabecero acolchado, madera de acacia.",
        "price": 11_500.00,
    },
    # Estantes / Armarios / Comodas
    {
        "sku": "LB-001",
        "name": "Librero Modular Oslo",
        "type": "Estanterias y libreros",
        "description": "Sistema modular de 5 niveles, pino barnizado natural.",
        "price": 3_100.00,
    },
    {
        "sku": "AR-001",
        "name": "Armario 3 Puertas Sliding",
        "type": "Closets y almacenamiento",
        "description": "Ropero con puertas corredizas y espejo incluido, 240 cm alto.",
        "price": 9_200.00,
    },
    {
        "sku": "CD-001",
        "name": "Comoda 6 Cajones Vintage",
        "type": "Recamaras",
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
                existing.subtitle = ft_data["subtitle"]
                existing.slug = ft_data["slug"]
                existing.image_url = ft_data["image_url"]
                existing.status = True

                print(f"  ♻️  Actualizado: {existing.title} (id={existing.id})")
                type_map[existing.title] = existing.id
            else:
                ft = FurnitureType(
                    title=ft_data["title"],
                    subtitle=ft_data["subtitle"],
                    slug=ft_data["slug"],
                    image_url=ft_data["image_url"],
                    status=True,
                )
                db.session.add(ft)
                db.session.flush()
                type_map[ft.title] = ft.id
                print(f"  ✅ Creado: {ft.title} (id={ft.id})")

        db.session.commit()

        # ── 2. Productos del seed ───────────────────────────────────────
        print("\n🪑 Sembrando productos...")
        seeded = 0
        updated = 0

        for p_data in PRODUCTS:
            furniture_type_id = type_map.get(p_data["type"])
            if not furniture_type_id:
                print(
                    f"  ❌ Sin tipo de mueble '{p_data['type']}' — se omite {p_data['sku']}"
                )
                continue

            existing = Product.query.filter_by(sku=p_data["sku"]).first()
            if existing:
                existing.name = p_data["name"]
                existing.furniture_type_id = furniture_type_id
                existing.description = p_data["description"]
                existing.price = p_data["price"]
                existing.status = True
                updated += 1
                print(f"  ♻️  Actualizado: {p_data['sku']} – {p_data['name']}")
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
            seeded += 1
            print(f"  ✅ {p_data['sku']} – {p_data['name']}  ${p_data['price']:,.2f}")

            db.session.commit()

        print(
            "\n✨ Siembra completa: "
            f"{seeded} insertado(s), {updated} actualizado(s).\n"
        )


if __name__ == "__main__":
    seed_products()
