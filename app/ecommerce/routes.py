"""Rutas iniciales para e-commerce."""

from flask import render_template

from . import ecommerce_bp
from .services import EcommerceService


@ecommerce_bp.route("/")
def home():
    """Página principal del e-commerce."""
    products = EcommerceService.get_featured_products()
    all_categories = EcommerceService.get_product_categories()
    featured_categories = EcommerceService.get_featured_categories()
    return render_template(
        "store/home.html",
        products=products,
        categories=all_categories,
        featured_categories=featured_categories,
        active_section="home",
    )


@ecommerce_bp.route("/cart")
def cart():
    """Carrito de compra (estructura inicial)."""
    return render_template("store/cart.html", active_section="cart")


@ecommerce_bp.route("/categories")
def categories():
    """Página de categorías completas."""
    all_categories = EcommerceService.get_product_categories()
    return render_template(
        "store/categories.html",
        categories=all_categories,
        active_section="categories",
    )
