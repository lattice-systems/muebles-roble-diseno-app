"""Seed idempotente de compras ecommerce iniciales con resenas/calificaciones.

Uso:
    venv/bin/python scripts/seed_ecommerce_orders_reviews.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from flask_security.utils import hash_password
from sqlalchemy import func, or_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.customer import Customer
from app.models.customer_user import CustomerUser
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment_method import PaymentMethod
from app.models.product import Product
from app.models.product_review import ProductReview

SEED_PREFIX = "seed:ecommerce:v1"
DEFAULT_PASSWORD = "SeedPass#123"

SEED_CUSTOMERS = [
    {
        "first_name": "Ana",
        "last_name": "Lopez",
        "email": "ana.ecommerce.seed@demo.com",
        "phone": "4771112201",
    },
    {
        "first_name": "Luis",
        "last_name": "Hernandez",
        "email": "luis.ecommerce.seed@demo.com",
        "phone": "4771112202",
    },
    {
        "first_name": "Carla",
        "last_name": "Mendoza",
        "email": "carla.ecommerce.seed@demo.com",
        "phone": "4771112203",
    },
]

SEED_ORDERS = [
    {
        "key": "ORD-A1",
        "customer_email": "ana.ecommerce.seed@demo.com",
        "status": "entregado",
        "payment_type": "pasarela_online",
        "product_positions": (0, 1),
        "quantities": (1, 2),
        "order_date": datetime(2026, 4, 4, 11, 20, 0),
    },
    {
        "key": "ORD-L1",
        "customer_email": "luis.ecommerce.seed@demo.com",
        "status": "enviado",
        "payment_type": "transferencia",
        "product_positions": (2, 3),
        "quantities": (1, 1),
        "order_date": datetime(2026, 4, 6, 9, 5, 0),
    },
    {
        "key": "ORD-C1",
        "customer_email": "carla.ecommerce.seed@demo.com",
        "status": "pendiente",
        "payment_type": "pasarela_online",
        "product_positions": (4, 5, 6),
        "quantities": (1, 1, 1),
        "order_date": datetime(2026, 4, 9, 16, 40, 0),
    },
    {
        "key": "ORD-A2",
        "customer_email": "ana.ecommerce.seed@demo.com",
        "status": "entregado",
        "payment_type": "transferencia",
        "product_positions": (7,),
        "quantities": (1,),
        "order_date": datetime(2026, 4, 10, 13, 15, 0),
    },
]

SEED_REVIEWS = [
    {
        "customer_email": "ana.ecommerce.seed@demo.com",
        "product_position": 0,
        "rating": 5,
        "review_text": "Muy buena calidad y el acabado se ve premium.",
    },
    {
        "customer_email": "ana.ecommerce.seed@demo.com",
        "product_position": 7,
        "rating": 4,
        "review_text": "Comoda y estable, la entrega fue puntual.",
    },
    {
        "customer_email": "luis.ecommerce.seed@demo.com",
        "product_position": 2,
        "rating": 5,
        "review_text": "Supero mis expectativas, bien empacado y armado.",
    },
    {
        "customer_email": "carla.ecommerce.seed@demo.com",
        "product_position": 4,
        "rating": 4,
        "review_text": "Buen diseno y materiales solidos para el precio.",
    },
]


def _to_decimal(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value))


def _normalized_email(email: str) -> str:
    return (email or "").strip().lower()


def _seed_email_variants(email: str) -> list[str]:
    canonical = _normalized_email(email)
    variants = [canonical]
    if canonical.endswith(".com"):
        variants.append(f"{canonical[:-4]}.local")
    elif canonical.endswith(".local"):
        variants.append(f"{canonical[:-6]}.com")
    return variants


def _get_active_products(minimum: int = 8) -> list[Product]:
    products = Product.query.filter_by(status=True).order_by(Product.id.asc()).all()
    if len(products) < minimum:
        raise RuntimeError(
            "No hay suficientes productos activos para seed ecommerce. "
            "Ejecuta scripts/seed_products.py y scripts/seed_inventory.py"
        )
    return products


def _get_payment_method_by_type(method_type: str) -> PaymentMethod | None:
    return (
        PaymentMethod.query.filter_by(
            status=True,
            available_ecommerce=True,
            type=method_type,
        )
        .order_by(PaymentMethod.id.asc())
        .first()
    )


def _get_default_ecommerce_payment_method() -> PaymentMethod:
    method = (
        PaymentMethod.query.filter_by(status=True, available_ecommerce=True)
        .order_by(PaymentMethod.id.asc())
        .first()
    )
    if method is None:
        raise RuntimeError(
            "No hay metodos de pago ecommerce activos. "
            "Ejecuta scripts/seed_payment_methods.py"
        )
    return method


def _get_or_create_customer_user(payload: dict) -> tuple[CustomerUser, bool]:
    email = _normalized_email(payload["email"])
    full_name = f"{payload['first_name']} {payload['last_name']}".strip()
    email_variants = _seed_email_variants(email)

    user = (
        CustomerUser.query.filter(func.lower(CustomerUser.email).in_(email_variants))
        .order_by(CustomerUser.id.asc())
        .first()
    )
    created = False
    if user is None:
        user = CustomerUser(
            full_name=full_name,
            email=email,
            password_hash=hash_password(DEFAULT_PASSWORD),
            status=True,
        )
        db.session.add(user)
        db.session.flush()
        created = True
    else:
        user.email = email
        user.full_name = full_name
        user.status = True

    return user, created


def _get_or_create_customer(
    payload: dict, customer_user_id: int
) -> tuple[Customer, bool]:
    email = _normalized_email(payload["email"])
    email_variants = _seed_email_variants(email)
    customer = (
        Customer.query.filter(func.lower(Customer.email).in_(email_variants))
        .order_by(Customer.id.asc())
        .first()
    )
    created = False

    if customer is None:
        customer = Customer(
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            email=email,
            phone=payload["phone"],
            status=True,
            requires_freight=False,
            user_id=customer_user_id,
        )
        db.session.add(customer)
        db.session.flush()
        created = True
    else:
        customer.first_name = payload["first_name"]
        customer.last_name = payload["last_name"]
        customer.email = email
        customer.phone = payload["phone"]
        customer.status = True
        if customer.user_id and customer.user_id != customer_user_id:
            raise RuntimeError(
                f"El customer {email} ya esta vinculado a otro customer_user."
            )
        customer.user_id = customer_user_id

    return customer, created


def _find_seed_order(order_key: str) -> Order | None:
    pattern = f"{SEED_PREFIX}:{order_key}%"
    matches = (
        Order.query.filter(
            Order.source == "ecommerce",
            Order.notes.isnot(None),
            Order.notes.like(pattern),
        )
        .order_by(Order.id.asc())
        .all()
    )

    if not matches:
        return None

    canonical = matches[0]
    for extra in matches[1:]:
        OrderItem.query.filter_by(order_id=extra.id).delete(synchronize_session=False)
        db.session.delete(extra)

    return canonical


def _upsert_seed_order(
    *,
    order_payload: dict,
    customer: Customer,
    customer_user: CustomerUser,
    products: list[Product],
    default_payment_method: PaymentMethod,
) -> tuple[Order, bool]:
    product_positions = tuple(order_payload["product_positions"])
    quantities = tuple(order_payload["quantities"])
    if len(product_positions) != len(quantities):
        raise RuntimeError(
            f"Orden seed {order_payload['key']} tiene product_positions/quantities inconsistentes."
        )

    payment_method = _get_payment_method_by_type(order_payload["payment_type"])
    if payment_method is None:
        payment_method = default_payment_method

    items_data: list[dict] = []
    total = Decimal("0.00")
    for position, qty in zip(product_positions, quantities):
        product = products[position % len(products)]
        quantity = max(1, int(qty))
        unit_price = _to_decimal(product.price or 0)
        items_data.append(
            {
                "product_id": product.id,
                "quantity": quantity,
                "price": unit_price,
            }
        )
        total += unit_price * quantity

    order_notes = (
        f"{SEED_PREFIX}:{order_payload['key']} "
        f"Compra ecommerce seed para demostracion."
    )
    order = _find_seed_order(order_payload["key"])
    created = False
    if order is None:
        order = Order(
            customer_id=customer.id,
            customer_user_id=customer_user.id,
            order_date=order_payload["order_date"],
            estimated_delivery_date=(
                order_payload["order_date"] + timedelta(days=14)
            ).date(),
            status=order_payload["status"],
            total=total,
            payment_method_id=payment_method.id,
            notes=order_notes,
            source="ecommerce",
        )
        db.session.add(order)
        db.session.flush()
        created = True
    else:
        order.customer_id = customer.id
        order.customer_user_id = customer_user.id
        order.order_date = order_payload["order_date"]
        order.estimated_delivery_date = (
            order_payload["order_date"] + timedelta(days=14)
        ).date()
        order.status = order_payload["status"]
        order.total = total
        order.payment_method_id = payment_method.id
        order.notes = order_notes
        order.source = "ecommerce"
        OrderItem.query.filter_by(order_id=order.id).delete(synchronize_session=False)

    for item in items_data:
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"],
            )
        )

    return order, created


def _customer_has_product_purchase(
    customer_user_id: int,
    customer_id: int,
    product_id: int,
) -> bool:
    match = (
        db.session.query(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(OrderItem.product_id == product_id)
        .filter(Order.status != "cancelado")
        .filter(
            or_(
                Order.customer_user_id == customer_user_id,
                Order.customer_id == customer_id,
            )
        )
        .first()
    )
    return match is not None


def _upsert_seed_review(
    *,
    review_payload: dict,
    customer_user: CustomerUser,
    customer: Customer,
    products: list[Product],
) -> tuple[ProductReview, bool]:
    product = products[review_payload["product_position"] % len(products)]
    if not _customer_has_product_purchase(customer_user.id, customer.id, product.id):
        raise RuntimeError(
            "No se puede crear reseña seed sin compra valida: "
            f"user={customer_user.email}, product_id={product.id}"
        )

    review = ProductReview.query.filter_by(
        product_id=product.id,
        customer_user_id=customer_user.id,
    ).first()
    created = False

    if review is None:
        review = ProductReview(
            product_id=product.id,
            customer_user_id=customer_user.id,
            rating=review_payload["rating"],
            review_text=review_payload["review_text"],
        )
        db.session.add(review)
        created = True
    else:
        review.rating = review_payload["rating"]
        review.review_text = review_payload["review_text"]

    return review, created


def seed_ecommerce_orders_and_reviews() -> None:
    products = _get_active_products(minimum=8)
    default_payment_method = _get_default_ecommerce_payment_method()

    customer_users_by_email: dict[str, CustomerUser] = {}
    customers_by_email: dict[str, Customer] = {}

    created_customer_users = 0
    created_customers = 0
    created_orders = 0
    created_reviews = 0

    for payload in SEED_CUSTOMERS:
        user, user_created = _get_or_create_customer_user(payload)
        customer, customer_created = _get_or_create_customer(payload, user.id)
        customer_users_by_email[_normalized_email(payload["email"])] = user
        customers_by_email[_normalized_email(payload["email"])] = customer
        created_customer_users += 1 if user_created else 0
        created_customers += 1 if customer_created else 0

    for order_payload in SEED_ORDERS:
        email = _normalized_email(order_payload["customer_email"])
        customer_user = customer_users_by_email[email]
        customer = customers_by_email[email]
        _, order_created = _upsert_seed_order(
            order_payload=order_payload,
            customer=customer,
            customer_user=customer_user,
            products=products,
            default_payment_method=default_payment_method,
        )
        created_orders += 1 if order_created else 0

    for review_payload in SEED_REVIEWS:
        email = _normalized_email(review_payload["customer_email"])
        customer_user = customer_users_by_email[email]
        customer = customers_by_email[email]
        _, review_created = _upsert_seed_review(
            review_payload=review_payload,
            customer_user=customer_user,
            customer=customer,
            products=products,
        )
        created_reviews += 1 if review_created else 0

    db.session.commit()

    total_seed_orders = (
        Order.query.filter(
            Order.source == "ecommerce",
            Order.notes.isnot(None),
            Order.notes.like(f"{SEED_PREFIX}%"),
        )
        .order_by(Order.id.asc())
        .count()
    )
    total_seed_reviews = (
        ProductReview.query.join(
            CustomerUser, CustomerUser.id == ProductReview.customer_user_id
        )
        .filter(
            CustomerUser.email.in_(
                [_normalized_email(x["email"]) for x in SEED_CUSTOMERS]
            )
        )
        .count()
    )

    print("\nSeed ecommerce (compras + resenas) ejecutado correctamente.")
    print(f"- Customer users creados: {created_customer_users}")
    print(f"- Customers creados: {created_customers}")
    print(f"- Ordenes ecommerce seed creadas: {created_orders}")
    print(f"- Resenas seed creadas: {created_reviews}")
    print(f"- Total ordenes seed detectadas: {total_seed_orders}")
    print(f"- Total resenas seed detectadas: {total_seed_reviews}\n")


def main() -> None:
    app = create_app()
    with app.app_context():
        seed_ecommerce_orders_and_reviews()


if __name__ == "__main__":
    main()
