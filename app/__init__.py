from flask import Flask

from config import Config
from .exceptions import register_error_handlers
from .extensions import csrf, db, migrate


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

    # Import models to register them with SQLAlchemy
    from . import models  # noqa: F401

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    from .login import login_bp

    app.register_blueprint(login_bp, url_prefix="/login")

    from .catalogs.colors import colors_bp

    app.register_blueprint(colors_bp, url_prefix="/colors")

    from .catalogs.roles import roles_bp

    app.register_blueprint(roles_bp, url_prefix="/roles")

    from .catalogs.wood_types import woods_types_bp

    app.register_blueprint(woods_types_bp, url_prefix="/wood-types")

    from .catalogs.unit_of_measures import unit_of_measures_bp

    app.register_blueprint(unit_of_measures_bp, url_prefix="/unit-of-measures")

    @app.route("/admin")
    def index_admin():
        from flask import render_template

        return render_template("layouts/admin.html")

    from .catalogs.furniture_type import furniture_type_bp

    app.register_blueprint(furniture_type_bp, url_prefix="/furniture-types")

    return app
