"""Servicios base para e-commerce."""

from __future__ import annotations

from app.models.furniture_type import FurnitureType


class EcommerceService:
    """Servicios para la vitrina de e-commerce."""

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
    def get_featured_products() -> list[dict[str, object]]:
        return EcommerceService.get_all_products()[:8]

    @staticmethod
    def get_all_products() -> list[dict[str, object]]:
        return [
            {
                "id": 1,
                "title": "Syltherine",
                "subtitle": "Silla de café moderna",
                "price": 2500,
                "original_price": 3500,
                "badge": "-30%",
                "image": "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&q=80&w=800",
                "images": [
                    "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&q=80&w=800",
                    "https://images.unsplash.com/photo-1592078615290-033ee584e267?auto=format&fit=crop&q=80&w=800",
                    "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&q=80&w=800",
                    "https://images.unsplash.com/photo-1592078615290-033ee584e267?auto=format&fit=crop&q=80&w=800",
                ],
                "description": "El sofá Asgaard es una obra maestra del diseño escandinavo, ofreciendo comodidad excepcional y un estilo moderno que se adapta a cualquier sala de estar. Creado en madera de pino y lino de alta resistencia.",
                "sizes": ["L", "XL", "XS"],
                "colors": ["purple", "black", "yellow"],
                "sku": "SY001",
                "category": "Sillas",
                "tags": ["Silla", "Café", "Hogar", "Tienda"],
                "url": "#",
            },
            {
                "id": 2,
                "title": "Leviosa",
                "subtitle": "Silla de café moderna",
                "price": 2500,
                "badge": None,
                "image": "https://images.unsplash.com/photo-1592078615290-033ee584e267?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 3,
                "title": "Lolito",
                "subtitle": "Sofá grande de lujo",
                "price": 7000,
                "original_price": 14000,
                "badge": "-50%",
                "image": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 4,
                "title": "Respira",
                "subtitle": "Mesa alta y banco para exterior",
                "price": 50000,
                "badge": "Nuevo",
                "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 5,
                "title": "Grifo",
                "subtitle": "Lámpara de noche",
                "price": 1500,
                "badge": None,
                "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 6,
                "title": "Muggo",
                "subtitle": "Taza pequeña",
                "price": 150,
                "badge": "Nuevo",
                "image": "https://images.unsplash.com/photo-1517254456976-ee8db7803e7d?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 7,
                "title": "Pingky",
                "subtitle": "Juego de cama encantador",
                "price": 7000,
                "original_price": 14000,
                "badge": "-50%",
                "image": "https://images.unsplash.com/photo-1505693314120-0d443867891c?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 8,
                "title": "Potty",
                "subtitle": "Maceta minimalista",
                "price": 500,
                "badge": "Nuevo",
                "image": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 99,
                "title": "Asgaard sofa",
                "subtitle": "Sofá de lujo",
                "price": 50000,
                "badge": None,
                "image": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=800",
                "images": [
                    "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=400",
                    "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&q=80&w=400",
                    "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&q=80&w=400",
                    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&q=80&w=400",
                ],
                "description": "Estableciendo un estándar como uno de los altavoces más potentes de su categoría, el Asgaard es un equipo compacto y robusto que ofrece un audio bien equilibrado, con medios claros y agudos extendidos que brindan una experiencia de sonido excepcional.",
                "sizes": ["L", "XL", "XS"],
                "colors": ["purple", "black", "yellow"],
                "sku": "SS001",
                "category": "Sofás",
                "tags": ["Sofá", "Silla", "Hogar", "Tienda"],
                "url": "#",
            },
        ]

    @staticmethod
    def get_product_by_id(product_id: int) -> dict[str, object] | None:
        products = EcommerceService.get_all_products()
        for p in products:
            if p.get("id") == product_id:
                return p
        return None

    @staticmethod
    def get_cart() -> dict:
        """Obtiene un carrito mock para las vistas de carrito y checkout."""
        # Tomando el Asgaard sofa (id 99) y Lolito (id 3)
        product1 = EcommerceService.get_product_by_id(99)
        product2 = EcommerceService.get_product_by_id(3)
        return {
            "cart_items": [
                {"product": product1, "quantity": 1, "subtotal": product1["price"] * 1},
                {"product": product2, "quantity": 1, "subtotal": product2["price"] * 1},
            ],
            "subtotal": product1["price"] + product2["price"],
            "total": product1["price"] + product2["price"],
        }
