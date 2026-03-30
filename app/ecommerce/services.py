"""Servicios base para e-commerce."""

from __future__ import annotations

import re
from math import ceil

from flask import session, url_for
from markupsafe import escape
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
    IVA_RATE = 0.16

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
                    "href": (
                        url_for(
                            "ecommerce.products",
                            type=cat.slug,
                            _anchor="products-results",
                        )
                        if cat.slug
                        else url_for("ecommerce.products")
                    ),
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
    def _highlight_match(value: object, search_term: str) -> str:
        """Subraya las coincidencias de búsqueda dentro de un texto."""
        text = str(value or "")
        needle = (search_term or "").strip()
        if not text:
            return ""
        if not needle:
            return str(escape(text))

        pattern = re.compile(re.escape(needle), re.IGNORECASE)
        parts: list[str] = []
        last_index = 0

        for match in pattern.finditer(text):
            parts.append(str(escape(text[last_index : match.start()])))
            parts.append(
                "<mark class='rounded px-0.5 bg-yellow-200/80 text-heading'>"
                f"{escape(match.group(0))}"
                "</mark>"
            )
            last_index = match.end()

        parts.append(str(escape(text[last_index:])))
        return "".join(parts)

    @staticmethod
    def search_catalogs_and_products(
        *,
        search_term: str = "",
        product_limit: int = 12,
    ) -> dict[str, object]:
        """Realiza búsqueda global en catálogos (furniture types) y productos."""
        normalized_search = (search_term or "").strip().lower()

        all_categories = EcommerceService.get_product_categories()
        all_products = EcommerceService.get_all_products()

        if not normalized_search:
            safe_product_limit = max(1, min(product_limit, 24))
            return {
                "search_term": "",
                "categories": [],
                "products": all_products[:safe_product_limit],
                "categories_total": 0,
                "products_total": len(all_products),
                "total_results": len(all_products),
            }

        filtered_categories = []
        for category in all_categories:
            candidate_fields = [
                ("Nombre", str(category.get("title", ""))),
                ("Subtítulo", str(category.get("subtitle", ""))),
                ("Slug", str(category.get("slug", ""))),
            ]

            matched_fields = []
            for label, raw_value in candidate_fields:
                if not raw_value.strip():
                    continue
                if normalized_search in raw_value.lower():
                    matched_fields.append(
                        {
                            "label": label,
                            "value": raw_value,
                            "highlighted": EcommerceService._highlight_match(
                                raw_value, search_term
                            ),
                        }
                    )

            if matched_fields:
                enriched_category = dict(category)
                enriched_category["matched_fields"] = matched_fields
                filtered_categories.append(enriched_category)

        filtered_products = []
        for product in all_products:
            tags_list = product.get("tags", []) or []
            tags_value = ", ".join(str(tag) for tag in tags_list if tag)
            candidate_fields = [
                ("Nombre", str(product.get("title", ""))),
                ("Subtítulo", str(product.get("subtitle", ""))),
                ("Categoría", str(product.get("category", ""))),
                ("Descripción", str(product.get("description", ""))),
                ("SKU", str(product.get("sku", ""))),
                ("Tags", tags_value),
            ]

            matched_fields = []
            for label, raw_value in candidate_fields:
                if not raw_value.strip():
                    continue
                if normalized_search in raw_value.lower():
                    matched_fields.append(
                        {
                            "label": label,
                            "value": raw_value,
                            "highlighted": EcommerceService._highlight_match(
                                raw_value, search_term
                            ),
                        }
                    )

            if matched_fields:
                enriched_product = dict(product)
                enriched_product["matched_fields"] = matched_fields
                filtered_products.append(enriched_product)

        safe_product_limit = max(1, min(product_limit, 24))
        limited_products = filtered_products[:safe_product_limit]

        return {
            "search_term": search_term.strip(),
            "categories": filtered_categories,
            "products": limited_products,
            "categories_total": len(filtered_categories),
            "products_total": len(filtered_products),
            "total_results": len(filtered_categories) + len(filtered_products),
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
    def _normalize_quantity(quantity: object, *, minimum: int = 1) -> int:
        try:
            parsed_quantity = int(quantity)
        except (TypeError, ValueError):
            return minimum
        return max(minimum, parsed_quantity)

    @staticmethod
    def _get_cart_store() -> dict[int, int]:
        raw_cart = session.get("ecommerce_cart", {})
        if not isinstance(raw_cart, dict):
            return {}

        normalized_cart: dict[int, int] = {}
        for product_id, quantity in raw_cart.items():
            try:
                parsed_product_id = int(product_id)
                parsed_quantity = int(quantity)
            except (TypeError, ValueError):
                continue

            if parsed_quantity > 0:
                normalized_cart[parsed_product_id] = parsed_quantity

        return normalized_cart

    @staticmethod
    def _save_cart_store(cart_store: dict[int, int]) -> None:
        session["ecommerce_cart"] = {
            str(product_id): quantity for product_id, quantity in cart_store.items()
        }
        session.modified = True

    @staticmethod
    def _get_stock_for_product(product_data: dict[str, object]) -> int:
        raw_stock = product_data.get("stock", 0)
        try:
            stock = int(raw_stock)
        except (TypeError, ValueError):
            stock = 0
        return max(0, stock)

    @staticmethod
    def add_product_to_cart(product_id: int, quantity: int = 1) -> dict[str, object]:
        product = EcommerceService.get_product_by_id(product_id)
        if not product:
            return EcommerceService.get_cart()

        max_stock = EcommerceService._get_stock_for_product(product)
        if max_stock <= 0:
            return EcommerceService.get_cart()

        safe_quantity = EcommerceService._normalize_quantity(quantity)
        cart_store = EcommerceService._get_cart_store()
        current_quantity = cart_store.get(product_id, 0)
        cart_store[product_id] = min(current_quantity + safe_quantity, max_stock)

        EcommerceService._save_cart_store(cart_store)
        return EcommerceService.get_cart()

    @staticmethod
    def update_product_quantity(product_id: int, quantity: int) -> dict[str, object]:
        cart_store = EcommerceService._get_cart_store()
        if product_id not in cart_store:
            return EcommerceService.get_cart()

        if quantity <= 0:
            cart_store.pop(product_id, None)
            EcommerceService._save_cart_store(cart_store)
            return EcommerceService.get_cart()

        product = EcommerceService.get_product_by_id(product_id)
        if not product:
            cart_store.pop(product_id, None)
            EcommerceService._save_cart_store(cart_store)
            return EcommerceService.get_cart()

        max_stock = EcommerceService._get_stock_for_product(product)
        if max_stock <= 0:
            cart_store.pop(product_id, None)
            EcommerceService._save_cart_store(cart_store)
            return EcommerceService.get_cart()

        cart_store[product_id] = min(
            EcommerceService._normalize_quantity(quantity), max_stock
        )
        EcommerceService._save_cart_store(cart_store)
        return EcommerceService.get_cart()

    @staticmethod
    def remove_product_from_cart(product_id: int) -> dict[str, object]:
        cart_store = EcommerceService._get_cart_store()
        if product_id in cart_store:
            cart_store.pop(product_id, None)
            EcommerceService._save_cart_store(cart_store)
        return EcommerceService.get_cart()

    @staticmethod
    def clear_cart() -> dict[str, object]:
        session.pop("ecommerce_cart", None)
        session.modified = True
        return EcommerceService.get_cart()

    @staticmethod
    def get_cart() -> dict:
        """Obtiene el carrito de sesión para vistas de carrito y checkout."""
        cart_store = EcommerceService._get_cart_store()
        if not cart_store:
            return {
                "cart_items": [],
                "subtotal": 0.0,
                "iva": 0.0,
                "total": 0.0,
                "total_items": 0,
                "iva_rate": EcommerceService.IVA_RATE,
            }

        cart_items: list[dict[str, object]] = []
        normalized_store: dict[int, int] = {}

        for product_id, requested_quantity in cart_store.items():
            product = EcommerceService.get_product_by_id(product_id)
            if not product:
                continue

            stock = EcommerceService._get_stock_for_product(product)
            if stock <= 0:
                continue

            safe_quantity = min(requested_quantity, stock)
            normalized_store[product_id] = safe_quantity
            price = float(product.get("price", 0) or 0)
            subtotal = round(price * safe_quantity, 2)

            cart_items.append(
                {
                    "product": product,
                    "quantity": safe_quantity,
                    "subtotal": subtotal,
                }
            )

        if normalized_store != cart_store:
            EcommerceService._save_cart_store(normalized_store)

        total_amount = round(sum(float(item["subtotal"]) for item in cart_items), 2)
        subtotal_amount = round(total_amount / (1 + EcommerceService.IVA_RATE), 2)
        iva_amount = round(total_amount - subtotal_amount, 2)
        total_items = sum(int(item["quantity"]) for item in cart_items)

        return {
            "cart_items": cart_items,
            "subtotal": subtotal_amount,
            "iva": iva_amount,
            "total": total_amount,
            "total_items": total_items,
            "iva_rate": EcommerceService.IVA_RATE,
        }
