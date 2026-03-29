"""Rutas iniciales para e-commerce."""

from flask import abort, render_template, request

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


@ecommerce_bp.route("/search")
def search():
    """Búsqueda global en catálogos y productos."""
    search_term = request.args.get("q", "", type=str)
    search_results = EcommerceService.search_catalogs_and_products(
        search_term=search_term,
        product_limit=12,
    )
    return render_template(
        "store/search.html",
        search_term=search_results["search_term"],
        categories=search_results["categories"],
        products=search_results["products"],
        categories_total=search_results["categories_total"],
        products_total=search_results["products_total"],
        total_results=search_results["total_results"],
        active_section="",
    )


@ecommerce_bp.route("/products")
def products():
    """Página de listado de productos con búsqueda y filtros."""
    search_term = request.args.get("q", "", type=str)
    type_slug = request.args.get("type", "", type=str)
    sort_by = request.args.get("sort", "default", type=str)
    limit = request.args.get("limit", 16, type=int) or 16
    page = request.args.get("page", 1, type=int) or 1

    filtered_catalog = EcommerceService.get_filtered_products(
        search_term=search_term,
        type_slug=type_slug,
        sort_by=sort_by,
        limit=limit,
        page=page,
    )
    all_categories = EcommerceService.get_product_categories()

    return render_template(
        "store/products.html",
        products=filtered_catalog["products"],
        categories=all_categories,
        total_products=filtered_catalog["total_products"],
        filtered_total=filtered_catalog["filtered_total"],
        filters={
            "q": filtered_catalog["search_term"],
            "type": filtered_catalog["type_slug"],
            "sort": filtered_catalog["sort_by"],
            "limit": filtered_catalog["limit"],
            "page": filtered_catalog["page"],
        },
        pagination={
            "page": filtered_catalog["page"],
            "total_pages": filtered_catalog["total_pages"],
            "has_prev": filtered_catalog["has_prev"],
            "has_next": filtered_catalog["has_next"],
            "prev_page": filtered_catalog["prev_page"],
            "next_page": filtered_catalog["next_page"],
            "start_item": filtered_catalog["start_item"],
            "end_item": filtered_catalog["end_item"],
            "page_numbers": filtered_catalog["page_numbers"],
        },
        limit_options=[8, 16, 24, 32, 48],
        active_section="products",
    )


@ecommerce_bp.route("/product/<int:product_id>")
def product(product_id: int):
    """Página de detalle de producto."""
    product_data = EcommerceService.get_product_by_id(product_id)
    if not product_data:
        featured_products = EcommerceService.get_featured_products()
        product_data = featured_products[0] if featured_products else None
    if not product_data:
        abort(404)

    related_products = [
        item
        for item in EcommerceService.get_featured_products()
        if item.get("id") != product_data.get("id")
    ][:4]

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
