"""Servicios base para e-commerce."""

from __future__ import annotations


class EcommerceService:
    """Contiene datos iniciales para la vitrina de e-commerce."""

    @staticmethod
    def get_product_categories() -> list[dict[str, str]]:
        return [
            {
                "title": "Salas",
                "subtitle": "Sofas, sillones individuales, loveseats",
                "image_url": "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Salas",
            },
            {
                "title": "Comedores",
                "subtitle": "Mesas de comedor, sillas de comedor, bancos",
                "image_url": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Comedores",
            },
            {
                "title": "Recamaras",
                "subtitle": "Camas, cabeceras, buros",
                "image_url": "https://images.unsplash.com/photo-1540518614846-7eded433c457?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Recamaras",
            },
            {
                "title": "Closets y almacenamiento",
                "subtitle": "Closets, roperos, armarios",
                "image_url": "https://images.unsplash.com/photo-1484101403633-562f891dc89a?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Closets y almacenamiento",
            },
            {
                "title": "Escritorios y oficina",
                "subtitle": "Escritorios, sillas de oficina, estaciones de trabajo",
                "image_url": "https://images.unsplash.com/photo-1486946255434-2466348c2166?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Escritorios y oficina",
            },
            {
                "title": "Muebles para TV",
                "subtitle": "Centros de entretenimiento, bases para TV, consolas",
                "image_url": "https://images.unsplash.com/photo-1615874959474-d609969a20ed?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Muebles para TV",
            },
            {
                "title": "Mesas",
                "subtitle": "Mesas de centro, mesas laterales, mesas auxiliares",
                "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Mesas",
            },
            {
                "title": "Estanterias y libreros",
                "subtitle": "Libreros, repisas, estantes",
                "image_url": "https://images.unsplash.com/photo-1594026112284-02bb6f3352fe?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Estanterias y libreros",
            },
            {
                "title": "Cocina",
                "subtitle": "Alacenas, islas de cocina, gabinetes",
                "image_url": "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Cocina",
            },
            {
                "title": "Muebles infantiles",
                "subtitle": "Camas infantiles, escritorios para ninos, organizadores",
                "image_url": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Muebles infantiles",
            },
            {
                "title": "Muebles decorativos",
                "subtitle": "Consolas decorativas, biombos, bancos decorativos",
                "image_url": "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Muebles decorativos",
            },
            {
                "title": "Muebles personalizados",
                "subtitle": "Disenos a medida, proyectos especiales, muebles bajo pedido",
                "image_url": "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Muebles personalizados",
            },
            {
                "title": "Muebles de jardin",
                "subtitle": "Salas de exterior, comedores de exterior, camastros y tumbonas",
                "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&q=80&w=800",
                "href": "#",
                "alt": "Muebles de jardin",
            },
        ]

    @staticmethod
    def get_featured_categories(limit: int = 3) -> list[dict[str, str]]:
        return EcommerceService.get_product_categories()[:limit]

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
