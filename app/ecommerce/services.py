"""Servicios base para e-commerce."""

from __future__ import annotations


class EcommerceService:
    """Contiene datos iniciales para la vitrina de e-commerce."""

    @staticmethod
    def get_featured_products() -> list[dict[str, object]]:
        return [
            {
                "id": 1,
                "title": "Syltherine",
                "subtitle": "Stylish cafe chair",
                "price": 2500,
                "original_price": 3500,
                "badge": "-30%",
                "image": "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 2,
                "title": "Leviosa",
                "subtitle": "Stylish cafe chair",
                "price": 2500,
                "badge": None,
                "image": "https://images.unsplash.com/photo-1592078615290-033ee584e267?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 3,
                "title": "Lolito",
                "subtitle": "Luxury big sofa",
                "price": 7000,
                "original_price": 14000,
                "badge": "-50%",
                "image": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 4,
                "title": "Respira",
                "subtitle": "Outdoor bar table and stool",
                "price": 500,
                "badge": "New",
                "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 5,
                "title": "Grifo",
                "subtitle": "Night lamp",
                "price": 1500,
                "original_price": None,
                "badge": None,
                "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 6,
                "title": "Muggo",
                "subtitle": "Small mug",
                "price": 150,
                "badge": "New",
                "image": "https://images.unsplash.com/photo-1517254456976-ee8db7803e7d?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 7,
                "title": "Pingky",
                "subtitle": "Cute bed set",
                "price": 7000,
                "original_price": 14000,
                "badge": "-50%",
                "image": "https://images.unsplash.com/photo-1505693314120-0d443867891c?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
            {
                "id": 8,
                "title": "Potty",
                "subtitle": "Minimalist flower pot",
                "price": 500,
                "badge": "New",
                "image": "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&q=80&w=800",
                "url": "#",
            },
        ]
