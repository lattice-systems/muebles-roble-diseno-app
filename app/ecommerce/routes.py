"""Rutas iniciales para e-commerce."""

from flask import render_template

from . import ecommerce_bp
from .services import EcommerceService


@ecommerce_bp.route("/")
def home():
    """Página principal del e-commerce."""
    products = EcommerceService.get_featured_products()
    return render_template(
        "store/home.html",
        products=products,
        active_section="home",
    )


@ecommerce_bp.route("/cart")
def cart():
    """Carrito de compra (estructura inicial)."""
    return render_template("store/cart.html", active_section="cart")
