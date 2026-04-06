"""
Fixtures centrales para la suite de pruebas.

Provee:
- ``app``: instancia Flask con TestingConfig (SQLite in-memory).
- ``db_session``: tablas creadas + session limpia por test.
- ``client``: Flask test client con session activa.
- ``seed_basic_data``: datos mínimos para arrancar (rol, usuario, tipo, producto, inventario, pago).
"""

from __future__ import annotations

import uuid

import pytest

from app import create_app
from app.extensions import db as _db
from config import TestingConfig

# ──────────────────── App & DB ────────────────────


@pytest.fixture(scope="session")
def app():
    """Crea la aplicación Flask una sola vez por sesión de tests."""
    application = create_app(config_class=TestingConfig)
    yield application


@pytest.fixture(autouse=True)
def db_session(app):
    """
    Crea todas las tablas antes de cada test y las limpia después.

    ``autouse=True`` garantiza que cada test arranca con DB limpia.
    """
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client con session habilitada."""
    return app.test_client()


# ──────────────────── Seed Data ────────────────────


@pytest.fixture()
def seed_basic_data(app, db_session):
    """
    Inserta datos mínimos requeridos por la mayoría de los tests:
    Role, User, FurnitureType, Product, ProductInventory, PaymentMethod.

    Returns:
        dict con las instancias creadas.
    """
    from app.models.furniture_type import FurnitureType
    from app.models.payment_method import PaymentMethod
    from app.models.product import Product
    from app.models.product_inventory import ProductInventory
    from app.models.role import Role
    from app.models.user import User
    from app.models.customer import Customer

    role = Role(name="admin", description="Administrador", status=True)
    db_session.add(role)
    db_session.flush()

    user = User(
        full_name="Test Admin",
        email="admin@test.com",
        password_hash="hashed_password_placeholder",
        fs_uniquifier=uuid.uuid4().hex,
        role_id=role.id,
        status=True,
    )
    db_session.add(user)
    db_session.flush()

    furniture_type = FurnitureType(
        title="Sillas",
        subtitle="Sillas de madera",
        image_url="https://example.com/sillas.jpg",
        slug="sillas",
        status=True,
    )
    db_session.add(furniture_type)
    db_session.flush()

    product = Product(
        sku="SILLA-001",
        name="Silla Rústica",
        furniture_type_id=furniture_type.id,
        description="Silla de madera de pino",
        price=1500.00,
        status=True,
    )
    db_session.add(product)
    db_session.flush()

    inventory = ProductInventory(
        product_id=product.id,
        stock=10,
    )
    db_session.add(inventory)

    payment_method = PaymentMethod(
        name="Efectivo",
        type="cash",
        description="Pago en efectivo",
        status=True,
        available_pos=True,
        available_ecommerce=True,
    )
    db_session.add(payment_method)

    customer = Customer(
        first_name="Juan",
        last_name="Pérez",
        email="juan@test.com",
        phone="4771234567",
        requires_freight=False,
        status=True,
    )
    db_session.add(customer)
    db_session.flush()

    db_session.commit()

    return {
        "role": role,
        "user": user,
        "furniture_type": furniture_type,
        "product": product,
        "inventory": inventory,
        "payment_method": payment_method,
        "customer": customer,
    }
