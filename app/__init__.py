from flask import Flask, redirect, request, url_for
from flask_security import SQLAlchemyUserDatastore, auth_required

from config import Config
from .exceptions import register_error_handlers
from .extensions import csrf, db, mail, migrate, security
from .rbac import register_rbac
from .security_events import (
    enforce_login_attempt_limit,
    process_login_attempt_response,
    register_security_event_handlers,
)


def create_app(config_class=None):
    """
    Factory de la aplicación Flask.

    Crea y configura la instancia de la aplicación Flask,
    inicializa extensiones y registra blueprints.

    Args:
        config_class: Clase de configuración a usar (default: Config).

    Returns:
        Flask: Instancia configurada de la aplicación
    """
    # Create Flask application
    app = Flask(__name__)

    # Initialize environment variables
    app.config.from_object(config_class or Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

    # Import models to register them with SQLAlchemy
    from . import models  # noqa: F401
    from .models import Role, User

    # Setup Flask-Security datastore
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)

    # Register RBAC deny-by-default guard and Jinja helpers
    register_rbac(app)

    @app.context_processor
    def inject_navbar_notifications():
        from flask_login import current_user

        from .shared.navbar_notifications import build_navbar_notifications

        if not getattr(current_user, "is_authenticated", False):
            return {
                "navbar_notifications": [],
                "navbar_notification_count": 0,
            }

        notification_data = build_navbar_notifications()
        return {
            "navbar_notifications": notification_data["items"],
            "navbar_notification_count": notification_data["count"],
        }

    @app.context_processor
    def inject_ecommerce_customer_user():
        from .customer_auth.decorators import get_current_customer_user

        return {
            "ecommerce_customer_user": get_current_customer_user(),
        }

    @app.context_processor
    def inject_ecommerce_cart():
        from .ecommerce.services import EcommerceService

        return {
            "cart": EcommerceService.get_cart(),
        }

    @app.context_processor
    def inject_admin_navigation_links():
        from .shared.admin_navigation import build_admin_navigation_links

        return {
            "admin_nav_links": build_admin_navigation_links(),
        }

    # Register auth/security event listeners (login/logout/password/access events)
    register_security_event_handlers(app)

    # Register error handlers
    register_error_handlers(app)

    @app.after_request
    def apply_auth_cache_control_headers(response):
        response = process_login_attempt_response(response)

        path = request.path or ""
        protected_prefixes = ("/admin", "/login", "/logout", "/reset", "/verify")

        if path.startswith(protected_prefixes):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    @app.before_request
    def enforce_security_login_attempts_limit():
        return enforce_login_attempt_limit()

    # Register blueprints
    from .login import login_bp

    app.register_blueprint(login_bp, url_prefix="/login")

    from .catalogs.colors import colors_bp

    from .users import users_bp

    app.register_blueprint(users_bp, url_prefix="/admin/users")

    from .suppliers import suppliers_bp

    app.register_blueprint(suppliers_bp, url_prefix="/admin/suppliers")

    from .purchases import purchases_bp

    app.register_blueprint(purchases_bp, url_prefix="/admin/purchases")

    from .costs import costs_bp

    app.register_blueprint(costs_bp, url_prefix="/admin/costs")

    from .reports import reports_bp

    app.register_blueprint(reports_bp, url_prefix="/admin/reports")

    from .audit import audit_bp

    app.register_blueprint(audit_bp, url_prefix="/admin/audit")

    from .security_audit import security_audit_bp

    app.register_blueprint(security_audit_bp, url_prefix="/admin/security-events")

    from .notifications import notifications_bp

    app.register_blueprint(notifications_bp, url_prefix="/admin/notifications")

    app.register_blueprint(colors_bp, url_prefix="/admin/catalogs/colors")

    from .catalogs.roles import roles_bp

    app.register_blueprint(roles_bp, url_prefix="/admin/catalogs/roles")

    from .catalogs.wood_types import woods_types_bp

    app.register_blueprint(woods_types_bp, url_prefix="/admin/catalogs/wood-types")

    from .catalogs.unit_of_measures import unit_of_measures_bp

    app.register_blueprint(
        unit_of_measures_bp, url_prefix="/admin/catalogs/unit-of-measures"
    )

    from .catalogs.payment_method import payment_method_bp

    app.register_blueprint(
        payment_method_bp, url_prefix="/admin/catalogs/payment-methods"
    )

    from .raw_materials import raw_materials_bp

    app.register_blueprint(raw_materials_bp, url_prefix="/admin/raw-materials")

    from .products import products_bp

    app.register_blueprint(products_bp, url_prefix="/admin/products")

    from .dashboard import dashboard_bp

    app.register_blueprint(dashboard_bp, url_prefix="/admin/dashboard")

    @app.route("/admin")
    @auth_required()
    def index_admin():
        return redirect(url_for("dashboard.index"))

    @app.route("/admin/catalogs")
    @auth_required()
    def catalogs_index():
        return redirect(url_for("colors.list_colors"))

    from .catalogs.furniture_type import furniture_type_bp

    app.register_blueprint(
        furniture_type_bp, url_prefix="/admin/catalogs/furniture-types"
    )

    from .ecommerce import ecommerce_bp

    app.register_blueprint(ecommerce_bp, url_prefix="/ecommerce")

    from .customer_auth import customer_auth_bp

    app.register_blueprint(customer_auth_bp, url_prefix="/ecommerce/account")

    @app.route("/")
    def index():
        return redirect(url_for("ecommerce.home"))

    from .sales import sales_bp

    app.register_blueprint(sales_bp, url_prefix="/admin/sales")

    from .customer_orders import customer_orders_bp

    app.register_blueprint(customer_orders_bp, url_prefix="/admin/customer-orders")

    from .contact_requests import contact_requests_bp

    app.register_blueprint(contact_requests_bp, url_prefix="/admin/contact-requests")

    from .production import production_bp

    app.register_blueprint(production_bp, url_prefix="/admin/production")

    return app
