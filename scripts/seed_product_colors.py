"""
Siembra colores base y relaciones producto-color.

Uso:
    python scripts/seed_product_colors.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.color import Color
from app.models.product import Product
from app.models.product_color import ProductColor
from seed_dataset import BASE_COLORS, PRODUCTS


def _build_palette_by_sku() -> dict[str, list[str]]:
    palette_by_sku: dict[str, list[str]] = {}
    for product in PRODUCTS:
        palette = [name for name in product.get("color_palette", []) if name]
        if palette:
            palette_by_sku[product["sku"]] = palette
    return palette_by_sku


def seed_product_colors():
    app = create_app()
    with app.app_context():
        color_ids_by_name: dict[str, int] = {}
        created_colors = 0
        updated_colors = 0

        for data in BASE_COLORS:
            color = Color.query.filter(
                db.func.lower(Color.name) == data["name"].lower()
            ).first()
            if not color:
                color = Color(
                    name=data["name"],
                    hex_code=data["hex_code"],
                    status=True,
                )
                db.session.add(color)
                db.session.flush()
                created_colors += 1
            else:
                color.hex_code = data["hex_code"]
                if not color.status:
                    updated_colors += 1
                color.status = True

            color_ids_by_name[color.name] = color.id

        palette_by_sku = _build_palette_by_sku()
        products = (
            Product.query.filter(Product.sku.in_(palette_by_sku.keys()))
            .order_by(Product.id)
            .all()
        )

        if not products:
            db.session.commit()
            print("\nNo hay productos para relacionar colores.\n")
            return

        created_relations = 0
        removed_relations = 0
        for product in products:
            target_names = palette_by_sku.get(product.sku, [])
            target_ids = {color_ids_by_name[name] for name in target_names}
            if not target_ids:
                continue

            existing_relations = ProductColor.query.filter_by(
                product_id=product.id
            ).all()
            existing_ids = {relation.color_id for relation in existing_relations}

            for relation in existing_relations:
                if relation.color_id not in target_ids:
                    db.session.delete(relation)
                    removed_relations += 1

            for color_id in target_ids - existing_ids:
                db.session.add(
                    ProductColor(
                        product_id=product.id,
                        color_id=color_id,
                    )
                )
                created_relations += 1

        # Productos fuera del dataset no deben conservar relaciones de color activas.
        legacy_products = Product.query.filter(
            ~Product.sku.in_(palette_by_sku.keys())
        ).all()
        for product in legacy_products:
            removed = ProductColor.query.filter_by(product_id=product.id).delete(
                synchronize_session=False
            )
            removed_relations += removed

        db.session.commit()
        print(
            f"\nColores creados: {created_colors}. "
            f"Colores reactivados/actualizados: {updated_colors}. "
            f"Relaciones producto-color creadas: {created_relations}. "
            f"Relaciones producto-color removidas: {removed_relations}.\n"
        )


if __name__ == "__main__":
    seed_product_colors()
