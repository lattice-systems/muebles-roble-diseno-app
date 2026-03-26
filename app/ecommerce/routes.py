"""Rutas iniciales para e-commerce."""

from flask import render_template

from . import ecommerce_bp
from .services import EcommerceService


@ecommerce_bp.context_processor
def inject_cart():
    """Hace que el carrito esté disponible globalmente para el cart_sidebar en todas las páginas."""
    return dict(cart=EcommerceService.get_cart())


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


@ecommerce_bp.route("/categories")
def categories():
    """Página de categorías completas (Tienda)."""
    all_categories = EcommerceService.get_product_categories()
    all_products = EcommerceService.get_all_products()
    return render_template(
        "store/categories.html",
        categories=all_categories,
        products=all_products,
        active_section="categories",
    )


@ecommerce_bp.route("/products")
def products():
    """Página de listado de todos los productos (Tienda/Shop)."""
    all_products = EcommerceService.get_all_products()
    return render_template(
        "store/products.html",
        products=all_products,
        active_section="products",
    )


@ecommerce_bp.route("/product/<int:product_id>")
def product(product_id: int):
    """Página de detalle de producto."""
    product_data = EcommerceService.get_product_by_id(product_id)
    if not product_data:
        # Fallback a un producto por defecto o error (simplificado aquí)
        product_data = EcommerceService.get_product_by_id(99)

    related_products = EcommerceService.get_featured_products()[:4]

    return render_template(
        "store/product.html",
        product=product_data,
        related_products=related_products,
        active_section="products",  # Maintain "Productos" highlighted in navbar
    )


@ecommerce_bp.route("/cart")
def cart():
    """Página del carrito de compras."""
    cart_data = EcommerceService.get_cart()
    return render_template("store/cart.html", cart=cart_data, active_section="")


@ecommerce_bp.route("/checkout")
def checkout():
    """Página de finalizar compra."""
    cart_data = EcommerceService.get_cart()
    return render_template("store/checkout.html", cart=cart_data, active_section="")


@ecommerce_bp.route("/contact")
def contact():
    """Página de contacto."""
    return render_template("store/contact.html", active_section="contact")


@ecommerce_bp.route("/about")
def about():
    """Página sobre nosotros."""
    return render_template("store/about.html", active_section="about")
