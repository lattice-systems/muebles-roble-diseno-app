"""
Script de siembra para productos y tipos de mueble.

Uso:
    .venv\\Scripts\\activate
    python scripts/seed_products.py
"""

import os
import sys
from collections import Counter
from csv import DictReader
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.furniture_type import FurnitureType
from app.models.product_image import ProductImage
from app.models.product import Product
from seed_dataset import CATEGORY_PRODUCT_TARGETS, FURNITURE_TYPES, PRODUCTS


def _validate_dataset_counts() -> None:
    counts = Counter(product["type"] for product in PRODUCTS)
    print("\n🔎 Validando distribucion de productos por categoria...")
    for category, target in CATEGORY_PRODUCT_TARGETS.items():
        current = counts.get(category, 0)
        status = "✅" if current == target else "⚠️"
        print(f"  {status} {category}: {current} producto(s), objetivo={target}")


def _load_official_product_images() -> dict[int, list[dict[str, str | int]]]:
    csv_path = Path(__file__).resolve().parents[1] / "docs" / "imagenes.csv"
    images_by_product_id: dict[int, list[dict[str, str | int]]] = {}

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            raw_product_id = (row.get("product_id") or "").strip()
            raw_sort_order = (row.get("sort_order") or "").strip()
            image_url = (row.get("image_url") or "").strip()
            public_id = (row.get("public_id") or "").strip()

            if (
                not raw_product_id
                or not raw_sort_order
                or not image_url
                or not public_id
            ):
                continue

            product_id = int(raw_product_id)
            sort_order = int(raw_sort_order)
            bucket = images_by_product_id.setdefault(product_id, [])
            bucket.append(
                {
                    "image_url": image_url,
                    "public_id": public_id,
                    "sort_order": sort_order,
                }
            )

    for product_id, images in images_by_product_id.items():
        images.sort(key=lambda image: image["sort_order"])
        sort_orders = [image["sort_order"] for image in images]
        if len(sort_orders) != len(set(sort_orders)):
            raise ValueError(
                "El archivo docs/imagenes.csv define sort_order duplicado para "
                f"product_id={product_id}."
            )
        if len(images) > 4:
            raise ValueError(
                "El archivo docs/imagenes.csv define más de 4 imágenes para "
                f"product_id={product_id}."
            )

    return images_by_product_id


def _seed_product_images(seed_products: list[Product]) -> tuple[int, int, int]:
    official_images_by_product_id = _load_official_product_images()
    created = 0
    updated = 0
    removed = 0

    product_by_id = {product.id: product for product in seed_products}
    seed_product_ids = set(product_by_id.keys())
    csv_product_ids = set(official_images_by_product_id.keys())

    missing_ids = sorted(csv_product_ids - seed_product_ids)
    if missing_ids:
        raise ValueError(
            "docs/imagenes.csv contiene product_id inexistentes en el seed de productos: "
            f"{missing_ids}"
        )

    for product in seed_products:
        official_images = official_images_by_product_id.get(product.id, [])
        existing_images = ProductImage.query.filter_by(product_id=product.id).all()
        existing_by_sort: dict[int, ProductImage] = {}
        duplicate_existing_images: list[ProductImage] = []
        for image in existing_images:
            if image.sort_order is None:
                duplicate_existing_images.append(image)
                continue
            if image.sort_order in existing_by_sort:
                duplicate_existing_images.append(image)
                continue
            existing_by_sort[image.sort_order] = image
        official_sort_orders = {int(image["sort_order"]) for image in official_images}
        duplicate_ids = {image.id for image in duplicate_existing_images if image.id}

        for image in duplicate_existing_images:
            db.session.delete(image)
            removed += 1

        for image in existing_images:
            if image.id in duplicate_ids:
                continue
            if image.sort_order not in official_sort_orders:
                db.session.delete(image)
                removed += 1

        for image_data in official_images:
            sort_order = int(image_data["sort_order"])
            existing = existing_by_sort.get(sort_order)
            if existing:
                changed = False
                if existing.image_url != image_data["image_url"]:
                    existing.image_url = str(image_data["image_url"])
                    changed = True
                if existing.public_id != image_data["public_id"]:
                    existing.public_id = str(image_data["public_id"])
                    changed = True
                if changed:
                    updated += 1
            else:
                db.session.add(
                    ProductImage(
                        product_id=product.id,
                        image_url=str(image_data["image_url"]),
                        public_id=str(image_data["public_id"]),
                        sort_order=sort_order,
                    )
                )
                created += 1

    legacy_removed = ProductImage.query.filter(
        ~ProductImage.product_id.in_(seed_product_ids)
    ).delete(synchronize_session=False)
    removed += legacy_removed

    return created, updated, removed


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

        seeded_products: list[Product] = []

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
                seeded_products.append(existing)
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
            seeded_products.append(product)
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

        # ── 3. Imágenes oficiales de productos ───────────────────────────
        print("\n🖼️  Sincronizando imágenes oficiales de productos...")
        images_created, images_updated, images_removed = _seed_product_images(
            seeded_products
        )
        db.session.commit()

        counts = Counter(product["type"] for product in PRODUCTS)

        print(
            "\n✨ Siembra completa: "
            f"{seeded} insertado(s), {updated} actualizado(s), {deactivated} desactivado(s)."
        )
        print("\n📊 Resumen de productos por categoria (catalogo inicial):")
        for category, qty in counts.items():
            print(f"  • {category}: {qty}")
        print(
            "\n🖼️  Imágenes: "
            f"{images_created} creada(s), {images_updated} actualizada(s), "
            f"{images_removed} removida(s)."
        )
        print()


if __name__ == "__main__":
    seed_products()
