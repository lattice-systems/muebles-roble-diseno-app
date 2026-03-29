"""Servicios base para e-commerce."""

from __future__ import annotations

from math import ceil

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
    def _resolve_images(product: Product) -> list[str]:
        """Resuelve imágenes con la regla: mínimo 1 y máximo 4."""
        candidates: list[str] = [EcommerceService._resolve_image(product)]

        for attr in ("images", "image_urls", "gallery_images", "photos"):
            value = getattr(product, attr, None)
            if not value:
                continue

            if isinstance(value, str):
                parsed_values = (
                    [segment.strip() for segment in value.split(",")]
                    if "," in value
                    else [value.strip()]
                )
            elif isinstance(value, (list, tuple, set)):
                parsed_values = list(value)
            else:
                continue

            for img in parsed_values:
                if isinstance(img, str) and img.strip():
                    candidates.append(img.strip())

        normalized_images: list[str] = []
        for img in candidates:
            if img and img not in normalized_images:
                normalized_images.append(img)

        if len(normalized_images) == 1:
            for fallback_img in EcommerceService.DEFAULT_PRODUCT_GALLERY[1:]:
                if fallback_img not in normalized_images:
                    normalized_images.append(fallback_img)
                if len(normalized_images) == 4:
                    break

        return normalized_images[:4] or [EcommerceService.DEFAULT_PRODUCT_IMAGE]

    @staticmethod
    def _serialize_product(product: Product) -> dict[str, object]:
        category = product.furniture_type.title if product.furniture_type else "General"
        type_slug = product.furniture_type.slug if product.furniture_type else ""
        subtitle = (
            product.furniture_type.subtitle
            if product.furniture_type and product.furniture_type.subtitle
            else f"Mueble de tipo {category.lower()}"
        )
        images = EcommerceService._resolve_images(product)
        image = images[0]
        stock = product.inventory_records[0].stock if product.inventory_records else 0
        color_names = [
            rel.color.name.lower()
            for rel in product.colors
            if rel.color and rel.color.name and rel.color.status
        ]
        color_palette = [
            {
                "name": rel.color.name,
                "hex": rel.color.hex_code,
            }
            for rel in product.colors
            if rel.color and rel.color.name and rel.color.status
        ]

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
            "color_palette": color_palette,
            "sku": product.sku,
            "stock": stock,
            "in_stock": stock > 0,
            "photo_count": len(images),
            "status": product.status,
            "furniture_type_id": product.furniture_type_id,
            "category": category,
            "type_slug": type_slug,
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
    def get_filtered_products(
        *,
        search_term: str = "",
        type_slug: str = "",
        sort_by: str = "default",
        limit: int = 16,
        page: int = 1,
    ) -> dict[str, object]:
        """Filtra y ordena productos para la vista de catálogo."""
        products = EcommerceService.get_all_products()
        total_products = len(products)

        normalized_search = (search_term or "").strip().lower()
        normalized_type = (type_slug or "").strip().lower()

        if normalized_type:
            products = [
                p
                for p in products
                if str(p.get("type_slug", "")).strip().lower() == normalized_type
            ]

        if normalized_search:
            filtered_products = []
            for product in products:
                tags = " ".join(product.get("tags", []) or [])
                searchable = " ".join(
                    [
                        str(product.get("title", "")),
                        str(product.get("subtitle", "")),
                        str(product.get("category", "")),
                        str(product.get("description", "")),
                        str(product.get("sku", "")),
                        tags,
                    ]
                ).lower()
                if normalized_search in searchable:
                    filtered_products.append(product)
            products = filtered_products

        if sort_by == "price_asc":
            products = sorted(products, key=lambda p: float(p.get("price", 0)))
        elif sort_by == "price_desc":
            products = sorted(
                products, key=lambda p: float(p.get("price", 0)), reverse=True
            )
        elif sort_by == "name_asc":
            products = sorted(products, key=lambda p: str(p.get("title", "")).lower())
        else:
            sort_by = "default"

        filtered_total = len(products)

        safe_limit = 16
        if isinstance(limit, int):
            safe_limit = max(1, min(limit, 48))

        total_pages = max(1, ceil(filtered_total / safe_limit))
        current_page = max(1, min(page if isinstance(page, int) else 1, total_pages))
        start_index = (current_page - 1) * safe_limit
        end_index = start_index + safe_limit
        paginated_products = products[start_index:end_index]

        start_item = start_index + 1 if filtered_total > 0 else 0
        end_item = min(start_index + len(paginated_products), filtered_total)

        page_window = 2
        start_page = max(1, current_page - page_window)
        end_page = min(total_pages, current_page + page_window)

        return {
            "products": paginated_products,
            "total_products": total_products,
            "filtered_total": filtered_total,
            "limit": safe_limit,
            "page": current_page,
            "total_pages": total_pages,
            "has_prev": current_page > 1,
            "has_next": current_page < total_pages,
            "prev_page": current_page - 1,
            "next_page": current_page + 1,
            "start_item": start_item,
            "end_item": end_item,
            "page_numbers": list(range(start_page, end_page + 1)),
            "search_term": search_term,
            "type_slug": type_slug,
            "sort_by": sort_by,
        }

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
