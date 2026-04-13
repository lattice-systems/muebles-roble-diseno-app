from flask import url_for


def build_admin_navigation_links() -> dict:
    return {
        "ecommerce": {
            "label": "E-commerce",
            "group": "Ventas",
            "keywords": "tienda ecommerce ventas online",
            "href": url_for("ecommerce.home"),
        }
    }
