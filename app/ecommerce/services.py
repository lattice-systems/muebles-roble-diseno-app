"""Servicios base para e-commerce."""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from math import ceil
from types import SimpleNamespace

from flask import session, url_for
from markupsafe import escape
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.customer import Customer
from app.models.furniture_type import FurnitureType
from app.models.payment_method import PaymentMethod
from app.models.product import Product
from app.models.product_color import ProductColor
from app.shared.inventory_service import InventoryService


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
    SHIPPING_REQUIRED_FIELDS = (
        "zip_code",
        "state",
        "city",
        "street",
        "neighborhood",
        "exterior_number",
    )

    @staticmethod
    def get_product_categories() -> list[dict[str, str]]:
        """Obtiene categorías desde la BD (furniture_types) con atributos e-commerce."""
        categories = (
            FurnitureType.query.filter_by(status=True).order_by(FurnitureType.id).all()
        )
        result = []
        for cat in categories:
            image_url = (cat.image_url or "").strip()
            if not image_url:
                continue

            result.append(
                {
                    "id": cat.id,
                    "title": cat.title,
                    "subtitle": cat.subtitle or "",
                    "image_url": image_url,
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
                joinedload(Product.images),
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
        candidates: list[str] = []

        relation_images = getattr(product, "images", None)
        if isinstance(relation_images, (list, tuple, set)):
            ordered_images = sorted(
                relation_images,
                key=lambda item: (
                    getattr(item, "sort_order", None) is None,
                    getattr(item, "sort_order", 0),
                    getattr(item, "id", 0),
                ),
            )
            for relation_image in ordered_images:
                if isinstance(relation_image, str):
                    image_url = relation_image.strip()
                else:
                    image_url = str(
                        getattr(relation_image, "image_url", "")
                        or getattr(relation_image, "url", "")
                    ).strip()
                if image_url:
                    candidates.append(image_url)

        resolved_primary_image = EcommerceService._resolve_image(product)
        if resolved_primary_image and (
            resolved_primary_image != EcommerceService.DEFAULT_PRODUCT_IMAGE
        ):
            candidates.append(resolved_primary_image)

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
            "specifications": product.specifications,
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

    @staticmethod
    def _to_decimal(value: object, default: Decimal = Decimal("0")) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return default

    @staticmethod
    def get_ecommerce_payment_methods() -> list[PaymentMethod]:
        return (
            PaymentMethod.query.filter_by(status=True, available_ecommerce=True)
            .order_by(PaymentMethod.id.asc())
            .all()
        )

    @staticmethod
    def quote_freight(
        *,
        delivery_mode: str,
        city: str,
        state: str,
        cart_total: Decimal | None = None,
    ) -> dict[str, object]:
        cart_total = cart_total or EcommerceService._to_decimal(
            EcommerceService.get_cart().get("total", 0)
        )

        if delivery_mode == "pickup":
            return {
                "cost": 0.0,
                "zone": None,
                "free": False,
                "delivery_days": 0,
                "reason": "Recoleccion en tienda",
                "total_with_freight": float(cart_total),
            }

        from app.sales.freight_config import calculate_freight

        pseudo_customer = SimpleNamespace(
            requires_freight=True,
            city=(city or "").strip(),
            state=(state or "").strip(),
        )
        freight = calculate_freight(pseudo_customer, cart_total)
        freight_cost = EcommerceService._to_decimal(freight.get("cost", 0))

        return {
            "cost": float(freight_cost),
            "zone": freight.get("zone"),
            "free": bool(freight.get("free", False)),
            "delivery_days": int(freight.get("delivery_days") or 0),
            "reason": freight.get("reason") or "",
            "total_with_freight": float(cart_total + freight_cost),
        }

    @staticmethod
    def _upsert_checkout_customer(
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        delivery_mode: str,
        shipping_data: dict[str, str],
    ) -> Customer:
        customer = Customer.query.filter(
            func.lower(Customer.email) == email.lower()
        ).first()

        if not customer:
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                status=True,
                requires_freight=(delivery_mode == "shipping"),
            )
            db.session.add(customer)

        customer.first_name = first_name
        customer.last_name = last_name
        customer.phone = phone

        if delivery_mode == "shipping":
            customer.requires_freight = True
            customer.zip_code = shipping_data.get("zip_code")
            customer.state = shipping_data.get("state")
            customer.city = shipping_data.get("city")
            customer.street = shipping_data.get("street")
            customer.neighborhood = shipping_data.get("neighborhood")
            customer.exterior_number = shipping_data.get("exterior_number")
            customer.interior_number = shipping_data.get("interior_number")
        elif customer.id is None:
            customer.requires_freight = False

        db.session.flush()
        return customer

    @staticmethod
    def checkout_from_form(form_data: dict) -> dict[str, object]:
        cart_data = EcommerceService.get_cart()
        if not cart_data["total_items"]:
            raise ValueError("Tu carrito esta vacio. Agrega productos para continuar.")

        first_name = (form_data.get("first_name") or "").strip()
        last_name = (form_data.get("last_name") or "").strip()
        email = (form_data.get("email") or "").strip().lower()
        phone = (form_data.get("phone") or "").strip()
        notes = (form_data.get("notes") or "").strip()
        delivery_mode = (form_data.get("delivery_mode") or "shipping").strip().lower()

        if not first_name or not last_name or not email or not phone:
            raise ValueError("Nombre, apellido, correo y telefono son obligatorios.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("El correo electronico no es valido.")
        if delivery_mode not in {"shipping", "pickup"}:
            raise ValueError("Selecciona un tipo de entrega valido.")

        payment_method_raw = form_data.get("payment_method_id")
        try:
            payment_method_id = int(str(payment_method_raw))
        except (TypeError, ValueError):
            raise ValueError("Selecciona un metodo de pago valido.")

        payment_method = PaymentMethod.query.filter_by(
            id=payment_method_id,
            status=True,
            available_ecommerce=True,
        ).first()
        if not payment_method:
            raise ValueError(
                "El metodo de pago seleccionado no esta disponible en ecommerce."
            )

        shipping_data = {
            "zip_code": (form_data.get("zip_code") or "").strip(),
            "state": (form_data.get("state") or "").strip(),
            "city": (form_data.get("city") or "").strip(),
            "street": (form_data.get("street") or "").strip(),
            "neighborhood": (form_data.get("neighborhood") or "").strip(),
            "exterior_number": (form_data.get("exterior_number") or "").strip(),
            "interior_number": (form_data.get("interior_number") or "").strip() or None,
        }

        if delivery_mode == "shipping":
            missing_labels = {
                "zip_code": "Codigo postal",
                "state": "Estado",
                "city": "Ciudad",
                "street": "Calle",
                "neighborhood": "Colonia",
                "exterior_number": "Numero exterior",
            }
            missing = [
                missing_labels[field]
                for field in EcommerceService.SHIPPING_REQUIRED_FIELDS
                if not shipping_data.get(field)
            ]
            if missing:
                raise ValueError(
                    "Faltan campos obligatorios de envio: " + ", ".join(missing) + "."
                )
            if not re.fullmatch(r"\d{5}", shipping_data["zip_code"]):
                raise ValueError("El codigo postal debe tener 5 digitos.")

        customer = EcommerceService._upsert_checkout_customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            delivery_mode=delivery_mode,
            shipping_data=shipping_data,
        )

        cart_items = cart_data["cart_items"]
        products_total = EcommerceService._to_decimal(
            sum(float(item["subtotal"]) for item in cart_items)
        )

        freight_data = EcommerceService.quote_freight(
            delivery_mode=delivery_mode,
            city=shipping_data.get("city", ""),
            state=shipping_data.get("state", ""),
            cart_total=products_total,
        )
        freight_cost = EcommerceService._to_decimal(freight_data.get("cost", 0))
        order_total = products_total + freight_cost

        normalized_items: list[dict[str, object]] = []

        for item in cart_items:
            product_payload = item.get("product") or {}
            product_id = int(product_payload.get("id"))
            quantity = int(item.get("quantity", 0))
            product_name = str(product_payload.get("title") or f"ID {product_id}")
            unit_price = EcommerceService._to_decimal(product_payload.get("price"))

            if quantity <= 0:
                raise ValueError(f"Cantidad invalida para '{product_name}'.")

            normalized_items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "price": float(unit_price),
                }
            )

        # Descontar stock usando servicio compartido
        for norm_item in normalized_items:
            product_payload = next(
                (
                    ci.get("product") or {}
                    for ci in cart_items
                    if int((ci.get("product") or {}).get("id", 0))
                    == norm_item["product_id"]
                ),
                {},
            )
            InventoryService.deduct_stock(
                product_id=norm_item["product_id"],
                quantity=norm_item["quantity"],
                product_name=str(
                    product_payload.get("title") or f"ID {norm_item['product_id']}"
                ),
            )

        estimated_delivery_date = date.today()
        delivery_days = int(freight_data.get("delivery_days") or 0)
        if delivery_days > 0:
            estimated_delivery_date = date.today() + timedelta(days=delivery_days)

        notes_parts = []
        if notes:
            notes_parts.append(notes)
        if delivery_mode == "shipping":
            notes_parts.append(
                "Entrega: envio a domicilio."
                + (f" {freight_data['reason']}" if freight_data.get("reason") else "")
            )
        else:
            notes_parts.append("Entrega: recoleccion en tienda.")

        # ── Datos de factura (opcional) ──
        requires_invoice = (form_data.get("requires_invoice") or "") == "1"
        if requires_invoice:
            rfc = (form_data.get("rfc") or "").strip().upper()
            business_name = (form_data.get("business_name") or "").strip()
            if not rfc or not re.fullmatch(r"[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}", rfc):
                raise ValueError(
                    "El RFC ingresado no es válido. "
                    "Verifica que tenga el formato correcto (ej. XAXX010101000)."
                )
            if not business_name:
                raise ValueError("La razón social es obligatoria para facturación.")
            notes_parts.append(f"[FACTURA] RFC: {rfc} | Razón social: {business_name}")

        final_notes = " ".join(notes_parts).strip()

        from app.customer_orders.services import CustomerOrderService

        try:
            order = CustomerOrderService.create_from_ecommerce(
                customer_id=customer.id,
                cart_items=normalized_items,
                payment_method_id=payment_method.id,
                total=order_total,
                notes=final_notes,
                estimated_delivery_date=estimated_delivery_date,
            )
        except Exception:
            db.session.rollback()
            raise

        return {
            "order": order,
            "customer": customer,
            "payment_method": payment_method,
            "freight": freight_data,
            "products_total": float(products_total),
            "total": float(order_total),
            "cart": cart_data,
        }
