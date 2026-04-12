from __future__ import annotations

import re

import pyotp
from flask_security.utils import hash_password, verify_password
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.customer import Customer
from app.models.customer_user import CustomerUser
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_review import ProductReview


class CustomerAuthService:
    """Servicios de autenticación y cuenta para cliente ecommerce."""

    @staticmethod
    def _normalize_email(raw_value: str) -> str:
        return (raw_value or "").strip().lower()

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", password):
            raise ValueError("La contraseña debe incluir al menos una mayúscula.")
        if not re.search(r"[a-z]", password):
            raise ValueError("La contraseña debe incluir al menos una minúscula.")
        if not re.search(r"\d", password):
            raise ValueError("La contraseña debe incluir al menos un número.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValueError(
                "La contraseña debe incluir al menos un carácter especial."
            )

    @staticmethod
    def register_customer_account(
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        password: str,
    ) -> tuple[CustomerUser, Customer]:
        first_name = (first_name or "").strip()
        last_name = (last_name or "").strip()
        phone = (phone or "").strip()
        email = CustomerAuthService._normalize_email(email)
        password = password or ""

        if not first_name or not last_name or not email or not phone:
            raise ValueError(
                "Nombre, apellido, correo y teléfono son obligatorios para crear la cuenta."
            )
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("El correo electrónico no es válido.")

        CustomerAuthService._validate_password(password)

        existing_user = CustomerUser.query.filter(
            func.lower(CustomerUser.email) == email.lower()
        ).first()
        if existing_user:
            raise ValueError("Ya existe una cuenta cliente con ese correo electrónico.")

        customer_user = CustomerUser(
            full_name=f"{first_name} {last_name}".strip(),
            email=email,
            password_hash=hash_password(password),
            status=True,
        )
        db.session.add(customer_user)
        db.session.flush()

        customer = Customer.query.filter(
            func.lower(Customer.email) == email.lower()
        ).first()
        if customer:
            if customer.user_id and customer.user_id != customer_user.id:
                raise ValueError("El cliente existente ya está asociado a otra cuenta.")
            customer.first_name = first_name
            customer.last_name = last_name
            customer.phone = phone
            customer.status = True
            customer.user_id = customer_user.id
        else:
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                requires_freight=False,
                status=True,
                user_id=customer_user.id,
            )
            db.session.add(customer)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("No se pudo crear la cuenta. Verifica los datos.")

        return customer_user, customer

    @staticmethod
    def authenticate_customer(email: str, password: str) -> CustomerUser | None:
        normalized_email = CustomerAuthService._normalize_email(email)
        if not normalized_email or not password:
            return None

        customer_user = CustomerUser.query.filter(
            func.lower(CustomerUser.email) == normalized_email
        ).first()
        if not customer_user or not customer_user.status:
            return None

        if not verify_password(password, customer_user.password_hash):
            return None

        return customer_user

    @staticmethod
    def is_2fa_enabled(customer_user: CustomerUser | None) -> bool:
        return bool(
            customer_user
            and customer_user.tf_primary_method == "authenticator"
            and customer_user.tf_totp_secret
        )

    @staticmethod
    def build_totp_uri(customer_user: CustomerUser, secret: str, issuer: str) -> str:
        return pyotp.TOTP(secret).provisioning_uri(
            name=customer_user.email,
            issuer_name=issuer,
        )

    @staticmethod
    def verify_totp_code(secret: str, token: str) -> bool:
        if not secret or not token:
            return False
        return bool(pyotp.TOTP(secret).verify((token or "").strip(), valid_window=1))

    @staticmethod
    def enable_2fa(customer_user: CustomerUser, secret: str) -> CustomerUser:
        customer_user.tf_primary_method = "authenticator"
        customer_user.tf_totp_secret = secret
        db.session.commit()
        return customer_user

    @staticmethod
    def disable_2fa(customer_user: CustomerUser) -> CustomerUser:
        customer_user.tf_primary_method = None
        customer_user.tf_totp_secret = None
        db.session.commit()
        return customer_user

    @staticmethod
    def get_linked_customer(customer_user: CustomerUser) -> Customer | None:
        return customer_user.customer

    @staticmethod
    def update_profile(customer_user: CustomerUser, data: dict) -> Customer:
        customer = CustomerAuthService.get_linked_customer(customer_user)
        if not customer:
            raise ValueError("No existe un perfil de cliente vinculado a esta cuenta.")

        customer.first_name = (
            data.get("first_name") or customer.first_name or ""
        ).strip()
        customer.last_name = (data.get("last_name") or customer.last_name or "").strip()
        customer.phone = (data.get("phone") or customer.phone or "").strip()

        delivery_mode = (data.get("delivery_mode") or "shipping").strip().lower()
        customer.requires_freight = delivery_mode == "shipping"

        customer.zip_code = (data.get("zip_code") or "").strip() or None
        customer.state = (data.get("state") or "").strip() or None
        customer.city = (data.get("city") or "").strip() or None
        customer.street = (data.get("street") or "").strip() or None
        customer.neighborhood = (data.get("neighborhood") or "").strip() or None
        customer.exterior_number = (data.get("exterior_number") or "").strip() or None
        customer.interior_number = (data.get("interior_number") or "").strip() or None

        customer_user.full_name = f"{customer.first_name} {customer.last_name}".strip()

        if not customer.first_name or not customer.last_name or not customer.phone:
            raise ValueError("Nombre, apellido y teléfono son obligatorios.")

        db.session.commit()
        return customer

    @staticmethod
    def get_orders_for_user(
        customer_user: CustomerUser, page: int = 1, per_page: int = 10
    ):
        filters = [Order.customer_user_id == customer_user.id]
        customer = CustomerAuthService.get_linked_customer(customer_user)
        if customer:
            filters.append(Order.customer_id == customer.id)

        query = Order.query.options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payment_method),
            selectinload(Order.customer),
        ).filter(or_(*filters))

        return query.order_by(Order.order_date.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

    @staticmethod
    def get_order_for_user(customer_user: CustomerUser, order_id: int) -> Order | None:
        filters = [Order.customer_user_id == customer_user.id]
        customer = CustomerAuthService.get_linked_customer(customer_user)
        if customer:
            filters.append(Order.customer_id == customer.id)

        return (
            Order.query.options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.payment_method),
                selectinload(Order.customer),
            )
            .filter(Order.id == order_id)
            .filter(or_(*filters))
            .first()
        )

    @staticmethod
    def has_purchased_product(customer_user: CustomerUser, product_id: int) -> bool:
        customer = CustomerAuthService.get_linked_customer(customer_user)
        owner_filters = [Order.customer_user_id == customer_user.id]
        if customer:
            owner_filters.append(Order.customer_id == customer.id)

        match = (
            db.session.query(OrderItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.product_id == product_id)
            .filter(Order.status != "cancelado")
            .filter(or_(*owner_filters))
            .first()
        )
        return match is not None

    @staticmethod
    def get_user_review_for_product(
        customer_user: CustomerUser,
        product_id: int,
    ) -> ProductReview | None:
        return ProductReview.query.filter_by(
            customer_user_id=customer_user.id,
            product_id=product_id,
        ).first()

    @staticmethod
    def get_recent_reviews_for_user(
        customer_user: CustomerUser,
        limit: int = 4,
    ) -> list[ProductReview]:
        safe_limit = max(1, min(limit, 12))
        return (
            ProductReview.query.options(selectinload(ProductReview.product))
            .filter(ProductReview.customer_user_id == customer_user.id)
            .order_by(ProductReview.updated_at.desc(), ProductReview.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def upsert_review(
        *,
        customer_user: CustomerUser,
        product_id: int,
        rating: int,
        review_text: str,
    ) -> ProductReview:
        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("El producto no existe.")

        try:
            safe_rating = int(rating)
        except (TypeError, ValueError):
            raise ValueError("La calificación debe ser un número entero del 1 al 5.")

        if safe_rating < 1 or safe_rating > 5:
            raise ValueError("La calificación debe estar entre 1 y 5 estrellas.")

        if not CustomerAuthService.has_purchased_product(customer_user, product_id):
            raise ValueError(
                "Solo puedes reseñar productos que hayas comprado previamente."
            )

        clean_review_text = (review_text or "").strip() or None
        review = ProductReview.query.filter_by(
            product_id=product_id,
            customer_user_id=customer_user.id,
        ).first()
        if review:
            review.rating = safe_rating
            review.review_text = clean_review_text
        else:
            review = ProductReview(
                product_id=product_id,
                customer_user_id=customer_user.id,
                rating=safe_rating,
                review_text=clean_review_text,
            )
            db.session.add(review)

        db.session.commit()
        return review
