"""
Script de siembra para productos y tipos de mueble.

Uso:
    .venv\\Scripts\\activate
    python scripts/seed_products.py
"""

import sys
import os
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.furniture_type import FurnitureType
from app.models.product import Product
from seed_dataset import CATEGORY_PRODUCT_TARGETS, FURNITURE_TYPES, PRODUCTS


def _validate_dataset_counts() -> None:
    counts = Counter(product["type"] for product in PRODUCTS)
    print("\n🔎 Validando distribucion de productos por categoria...")
    for category, target in CATEGORY_PRODUCT_TARGETS.items():
        current = counts.get(category, 0)
        status = "✅" if current == target else "⚠️"
        print(f"  {status} {category}: {current} producto(s), objetivo={target}")


def seed_products():
    app = create_app()
    with app.app_context():
        _validate_dataset_counts()

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
        deactivated = 0

        seed_skus = {item["sku"] for item in PRODUCTS}

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

        # Mantener coherente el catalogo inicial: productos fuera del seed quedan inactivos.
        legacy_products = Product.query.filter(
            Product.status.is_(True),
            ~Product.sku.in_(seed_skus),
        ).all()
        for legacy in legacy_products:
            legacy.status = False
            deactivated += 1

        db.session.commit()

        counts = Counter(product["type"] for product in PRODUCTS)

        print(
            "\n✨ Siembra completa: "
            f"{seeded} insertado(s), {updated} actualizado(s), {deactivated} desactivado(s)."
        )
        print("\n📊 Resumen de productos por categoria (catalogo inicial):")
        for category, qty in counts.items():
            print(f"  • {category}: {qty}")
        print()


if __name__ == "__main__":
    seed_products()
