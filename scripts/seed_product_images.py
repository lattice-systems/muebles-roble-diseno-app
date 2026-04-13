"""Seed idempotente de imagenes de producto.

Lee el dataset en scripts/seed_product_images.json y sincroniza la tabla
product_images por SKU y sort_order.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.product import Product
from app.models.product_image import ProductImage

DATA_FILE = Path(__file__).with_name("seed_product_images.json")
PUBLIC_ID_REGEX = re.compile(r"/upload/(?:v\\d+/)?(.+?)(?:\\.[A-Za-z0-9]+)?(?:\\?.*)?$")


def _extract_public_id(image_url: str) -> str | None:
    match = PUBLIC_ID_REGEX.search(image_url)
    if not match:
        return None
    return match.group(1)


def _load_images_by_sku() -> dict[str, list[str]]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"No existe el dataset de imagenes: {DATA_FILE}")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El dataset de imagenes debe ser un objeto SKU -> [urls]")

    images_by_sku: dict[str, list[str]] = {}
    for raw_sku, raw_urls in data.items():
        if not isinstance(raw_sku, str) or not isinstance(raw_urls, list):
            continue

        sku = raw_sku.strip().upper()
        urls = [url.strip() for url in raw_urls if isinstance(url, str) and url.strip()]
        if sku and urls:
            images_by_sku[sku] = urls

    return images_by_sku


def seed_product_images() -> None:
    images_by_sku = _load_images_by_sku()
    app = create_app()

    with app.app_context():
        target_skus = list(images_by_sku.keys())
        products = Product.query.filter(Product.sku.in_(target_skus)).all()
        products_by_sku = {product.sku: product for product in products}

        missing_skus = sorted(set(target_skus) - set(products_by_sku.keys()))
        created = 0
        updated = 0
        removed = 0

        for sku, target_urls in images_by_sku.items():
            product = products_by_sku.get(sku)
            if product is None:
                continue

            existing_rows = (
                ProductImage.query.filter_by(product_id=product.id)
                .order_by(ProductImage.sort_order.asc(), ProductImage.id.asc())
                .all()
            )

            existing_by_sort: dict[int, ProductImage] = {}
            for row in existing_rows:
                sort_key = row.sort_order if row.sort_order is not None else -1
                if sort_key in existing_by_sort:
                    db.session.delete(row)
                    removed += 1
                    continue
                existing_by_sort[sort_key] = row

            for sort_order, image_url in enumerate(target_urls, start=1):
                public_id = _extract_public_id(image_url)
                row = existing_by_sort.pop(sort_order, None)

                if row is None:
                    db.session.add(
                        ProductImage(
                            product_id=product.id,
                            image_url=image_url,
                            public_id=public_id,
                            sort_order=sort_order,
                        )
                    )
                    created += 1
                    continue

                changed = False
                if row.image_url != image_url:
                    row.image_url = image_url
                    changed = True
                if row.public_id != public_id:
                    row.public_id = public_id
                    changed = True
                if row.sort_order != sort_order:
                    row.sort_order = sort_order
                    changed = True
                if changed:
                    updated += 1

            for row in existing_by_sort.values():
                db.session.delete(row)
                removed += 1

        # Mantener dataset consistente: si un producto no esta en el seed,
        # eliminamos sus imagenes para evitar residuos de datos legacy.
        legacy_products = Product.query.filter(~Product.sku.in_(target_skus)).all()
        for legacy_product in legacy_products:
            removed += ProductImage.query.filter_by(
                product_id=legacy_product.id
            ).delete(synchronize_session=False)

        db.session.commit()

        print("\nSeed de imagenes de producto ejecutado correctamente.")
        print(f"- Productos en dataset: {len(images_by_sku)}")
        print(f"- Registros creados: {created}")
        print(f"- Registros actualizados: {updated}")
        print(f"- Registros eliminados: {removed}")
        if missing_skus:
            print(f"- SKUs no encontrados en products: {', '.join(missing_skus)}")


if __name__ == "__main__":
    seed_product_images()
