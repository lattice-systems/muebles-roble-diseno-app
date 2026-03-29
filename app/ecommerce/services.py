"""Servicios base para e-commerce."""

from __future__ import annotations

from flask import url_for
from sqlalchemy.orm import joinedload

from app.models.furniture_type import FurnitureType
from app.models.product import Product
from app.models.product_color import ProductColor


class EcommerceService:
    """Servicios para la vitrina de e-commerce."""

    DEFAULT_PRODUCT_IMAGE = (
        "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e"
        "?auto=format&fit=crop&q=80&w=800"
    )
    DEFAULT_PRODUCT_GALLERY = [
        "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=400",
        "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&q=80&w=400",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&q=80&w=400",
        "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&q=80&w=400",
    ]

    @staticmethod
    def get_product_categories() -> list[dict[str, str]]:
        """Obtiene categorías desde la BD (furniture_types) con atributos e-commerce."""
        categories = (
            FurnitureType.query.filter_by(status=True).order_by(FurnitureType.id).all()
        )
        result = []
        for cat in categories:
            result.append(
                {
                    "id": cat.id,
                    "title": cat.title,
                    "subtitle": cat.subtitle or "",
                    "image_url": cat.image_url or "#",
                    "href": f"/products?type={cat.slug}" if cat.slug else "#",
                    "alt": cat.title,
                    "slug": cat.slug,
                }
            )
        return result

    @staticmethod
    def get_featured_categories(limit: int = 3) -> list[dict[str, str]]:
        return EcommerceService.get_product_categories()[:limit]

    @staticmethod
    def _query_products():
        return (
            Product.query.options(
                joinedload(Product.furniture_type),
                joinedload(Product.colors).joinedload(ProductColor.color),
                joinedload(Product.inventory_records),
            )
            .filter(Product.status.is_(True))
            .order_by(Product.id.desc())
        )

    @staticmethod
    def _resolve_image(product: Product) -> str:
        # Preparado para cuando el modelo agregue un campo de imagen real.
        for attr in ("image_url", "image", "main_image", "thumbnail_url"):
            value = getattr(product, attr, None)
            if value:
                return value
        return EcommerceService.DEFAULT_PRODUCT_IMAGE

    @staticmethod
    def _serialize_product(product: Product) -> dict[str, object]:
        category = product.furniture_type.title if product.furniture_type else "General"
        subtitle = (
            product.furniture_type.subtitle
            if product.furniture_type and product.furniture_type.subtitle
            else f"Mueble de tipo {category.lower()}"
        )
        image = EcommerceService._resolve_image(product)
        images = [image] + EcommerceService.DEFAULT_PRODUCT_GALLERY[1:]
        stock = product.inventory_records[0].stock if product.inventory_records else 0
        color_names = [
            rel.color.name.lower()
            for rel in product.colors
            if rel.color and rel.color.name and rel.color.status
        ]
        tags = [category, "Hogar", "Tienda"]

        return {
            "id": product.id,
            "title": product.name,
            "subtitle": subtitle,
            "price": float(product.price or 0),
            "original_price": None,
            "badge": "Nuevo" if stock > 0 else None,
            "image": image,
            "images": images,
            "description": product.description,
            "sizes": ["S", "M", "L"],
            "colors": color_names,
            "sku": product.sku,
            "category": category,
            "tags": tags,
            "url": url_for("ecommerce.product", product_id=product.id),
        }

    @staticmethod
    def get_featured_products() -> list[dict[str, object]]:
        products = EcommerceService._query_products().limit(8).all()
        return [EcommerceService._serialize_product(product) for product in products]

    @staticmethod
    def get_all_products() -> list[dict[str, object]]:
        products = EcommerceService._query_products().all()
        return [EcommerceService._serialize_product(product) for product in products]

    @staticmethod
    def get_product_by_id(product_id: int) -> dict[str, object] | None:
        product = (
            EcommerceService._query_products().filter(Product.id == product_id).first()
        )
        if not product:
            return None
        return EcommerceService._serialize_product(product)

    @staticmethod
    def get_cart() -> dict:
        """Obtiene un carrito mock para las vistas de carrito y checkout."""
        products = EcommerceService.get_featured_products()
        product1 = products[0] if len(products) > 0 else None
        product2 = products[1] if len(products) > 1 else product1

        if not product1:
            return {"cart_items": [], "subtotal": 0, "total": 0}

        cart_items = [
            {"product": product1, "quantity": 1, "subtotal": product1["price"] * 1}
        ]
        if product2 and product2["id"] != product1["id"]:
            cart_items.append(
                {"product": product2, "quantity": 1, "subtotal": product2["price"] * 1}
            )

        subtotal = sum(item["subtotal"] for item in cart_items)
        return {
            "cart_items": cart_items,
            "subtotal": subtotal,
            "total": subtotal,
        }
