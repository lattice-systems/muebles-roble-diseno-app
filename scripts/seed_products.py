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
from seed_dataset import (
    BOM_TEMPLATES,
    CATEGORY_PRODUCT_TARGETS,
    FURNITURE_TYPES,
    PRODUCTS,
    RAW_MATERIALS,
)
from seed_pricing_rules import (
    PriceQuote,
    build_material_catalog,
    build_price_quote,
    load_images_by_sku,
)


def _validate_dataset_counts() -> None:
    counts = Counter(product["type"] for product in PRODUCTS)
    print("\n🔎 Validando distribucion de productos por categoria...")
    for category, target in CATEGORY_PRODUCT_TARGETS.items():
        current = counts.get(category, 0)
        status = "✅" if current == target else "⚠️"
        print(f"  {status} {category}: {current} producto(s), objetivo={target}")


def _build_price_quotes() -> dict[str, PriceQuote]:
    images_by_sku = load_images_by_sku()
    material_catalog = build_material_catalog(RAW_MATERIALS)

    quotes_by_sku: dict[str, PriceQuote] = {}
    errors: list[str] = []

    for product_data in PRODUCTS:
        sku = product_data["sku"]
        template_name = product_data.get("bom_template")
        template = BOM_TEMPLATES.get(template_name)

        if not template:
            errors.append(
                f"{sku}: no se encontro bom_template '{template_name}' en BOM_TEMPLATES"
            )
            continue

        try:
            quote = build_price_quote(
                product_data=product_data,
                base_template=template,
                image_urls=images_by_sku.get(sku, []),
                material_catalog=material_catalog,
            )
            quotes_by_sku[sku] = quote
        except Exception as exc:
            errors.append(f"{sku}: {exc}")

    if errors:
        joined_errors = "\n- ".join(errors)
        raise RuntimeError(
            "Se detectaron incoherencias de fidelidad en el catalogo seed:\n"
            f"- {joined_errors}"
        )

    return quotes_by_sku


def seed_products():
    app = create_app()
    with app.app_context():
        _validate_dataset_counts()
        price_quotes = _build_price_quotes()

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

            quote = price_quotes.get(p_data["sku"])
            if quote is None:
                print(f"  ❌ Sin cotizacion de precio para {p_data['sku']} — se omite")
                continue

            existing = Product.query.filter_by(sku=p_data["sku"]).first()
            if existing:
                existing.name = p_data["name"]
                existing.furniture_type_id = furniture_type_id
                existing.description = p_data["description"]
                existing.specifications = p_data.get("specifications", "")
                existing.price = quote.sale_price
                existing.status = True
                updated += 1
                print(
                    f"  ♻️  Actualizado: {p_data['sku']} – {p_data['name']} "
                    f"${quote.sale_price:,.2f}"
                )
                continue

            product = Product(
                sku=p_data["sku"],
                name=p_data["name"],
                furniture_type_id=furniture_type_id,
                description=p_data["description"],
                specifications=p_data.get("specifications", ""),
                price=quote.sale_price,
                status=True,
            )
            db.session.add(product)
            seeded += 1
            print(f"  ✅ {p_data['sku']} – {p_data['name']}  ${quote.sale_price:,.2f}")

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
