from flask import Flask
from flask_security import SQLAlchemyUserDatastore, auth_required

from config import Config
from .exceptions import register_error_handlers
from .extensions import csrf, db, mail, migrate, security


def create_app():
    """
    Factory de la aplicación Flask.

    Crea y configura la instancia de la aplicación Flask,
    inicializa extensiones y registra blueprints.

    Returns:
        Flask: Instancia configurada de la aplicación
    """
    # Create Flask application
    app = Flask(__name__)

    # Initialize environment variables
    app.config.from_object(Config)

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

    # Register error handlers
    register_error_handlers(app)

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

    app.register_blueprint(costs_bp, url_prefix="/costs")

    app.register_blueprint(colors_bp, url_prefix="/colors")

    from .catalogs.roles import roles_bp

    app.register_blueprint(roles_bp, url_prefix="/roles")

    from .catalogs.wood_types import woods_types_bp

    app.register_blueprint(woods_types_bp, url_prefix="/wood-types")

    from .catalogs.unit_of_measures import unit_of_measures_bp

    app.register_blueprint(unit_of_measures_bp, url_prefix="/unit-of-measures")

    from .catalogs.payment_method import payment_method_bp

    app.register_blueprint(payment_method_bp, url_prefix="/payment-methods")

    from .suppliers.raw_materials import raw_materials_bp

    app.register_blueprint(raw_materials_bp, url_prefix="/raw-materials")

    from .products import products_bp

    app.register_blueprint(products_bp, url_prefix="/products")

    @app.route("/admin")
    @auth_required()
    def index_admin():
        from flask import render_template

        return render_template("layouts/admin.html")

    from .catalogs.furniture_type import furniture_type_bp

    app.register_blueprint(furniture_type_bp, url_prefix="/furniture-types")

    from .ecommerce import ecommerce_bp

    app.register_blueprint(ecommerce_bp, url_prefix="/ecommerce")

    from .sales import sales_bp

    app.register_blueprint(sales_bp, url_prefix="/sales")

    return app
