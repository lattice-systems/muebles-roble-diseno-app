"""
Siembra colores base y relaciones producto-color.

Uso:
    python scripts/seed_product_colors.py
"""

import os
import random
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.color import Color
from app.models.product import Product
from app.models.product_color import ProductColor

BASE_COLORS = [
    {"name": "Blanco", "hex_code": "#F5F5F5"},
    {"name": "Negro", "hex_code": "#1F2937"},
    {"name": "Gris", "hex_code": "#9CA3AF"},
    {"name": "Marrón", "hex_code": "#8B5E3C"},
    {"name": "Beige", "hex_code": "#D6C6A8"},
    {"name": "Azul Marino", "hex_code": "#1E3A8A"},
    {"name": "Verde Oliva", "hex_code": "#6B8E23"},
    {"name": "Terracota", "hex_code": "#B95D3C"},
]

CATEGORY_COLOR_HINTS = {
    "Silla": ["Negro", "Gris", "Marrón"],
    "Mesa": ["Marrón", "Beige", "Negro"],
    "Sofa": ["Gris", "Beige", "Azul Marino"],
    "Cama": ["Beige", "Gris", "Blanco"],
    "Estante": ["Marrón", "Negro", "Blanco"],
    "Armario": ["Marrón", "Blanco", "Gris"],
    "Escritorio": ["Marrón", "Negro", "Gris"],
    "Comoda": ["Marrón", "Beige", "Blanco"],
}


def seed_product_colors():
    app = create_app()
    with app.app_context():
        color_ids_by_name: dict[str, int] = {}
        created_colors = 0

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
            elif not color.status:
                color.status = True

            color_ids_by_name[color.name] = color.id

        products = Product.query.order_by(Product.id).all()
        if not products:
            db.session.commit()
            print("\nNo hay productos para relacionar colores.\n")
            return

        created_relations = 0
        for product in products:
            existing_relations = ProductColor.query.filter_by(
                product_id=product.id
            ).count()
            if existing_relations > 0:
                continue

            category = (
                product.furniture_type.title if product.furniture_type else "General"
            )
            suggested_names = CATEGORY_COLOR_HINTS.get(
                category, ["Gris", "Marrón", "Negro"]
            )
            selectable = [name for name in suggested_names if name in color_ids_by_name]

            if len(selectable) < 2:
                selectable = list(color_ids_by_name.keys())

            chosen_count = min(3, max(2, len(selectable)))
            chosen_names = random.sample(selectable, k=chosen_count)

            for name in chosen_names:
                db.session.add(
                    ProductColor(
                        product_id=product.id,
                        color_id=color_ids_by_name[name],
                    )
                )
                created_relations += 1

        db.session.commit()
        print(
            f"\nColores creados: {created_colors}. "
            f"Relaciones producto-color creadas: {created_relations}.\n"
        )


if __name__ == "__main__":
    seed_product_colors()
