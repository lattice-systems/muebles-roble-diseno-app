"""Pruebas de integracion para cuenta cliente en ecommerce."""

from __future__ import annotations

from flask_security.utils import hash_password

from app.models.customer_user import CustomerUser
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_review import ProductReview


def _login_customer_session(client, customer_user_id: int):
    with client.session_transaction() as session:
        session["ecommerce_customer_user_id"] = customer_user_id


class TestCustomerAccountAuth:
    def test_register_creates_customer_user_and_links_customer(
        self,
        client,
        app,
        db_session,
        seed_basic_data,
    ):
        response = client.post(
            "/ecommerce/account/register",
            data={
                "first_name": "Ana",
                "last_name": "Lopez",
                "email": "ana.customer@test.com",
                "phone": "4770001122",
                "password": "TestPass#123",
            },
            follow_redirects=False,
        )

        assert response.status_code in (302, 303)
        assert "/ecommerce/account/dashboard" in response.headers.get("Location", "")

        with app.app_context():
            user = CustomerUser.query.filter_by(email="ana.customer@test.com").first()
            assert user is not None
            assert user.customer is not None
            assert user.customer.email == "ana.customer@test.com"

    def test_login_dashboard_and_logout_flow(
        self, client, app, db_session, seed_basic_data
    ):
        with app.app_context():
            customer = seed_basic_data["customer"]
            customer_user = CustomerUser(
                full_name=f"{customer.first_name} {customer.last_name}",
                email=customer.email,
                password_hash=hash_password("TestPass#123"),
                status=True,
            )
            db_session.add(customer_user)
            db_session.flush()
            customer.user_id = customer_user.id
            db_session.commit()
            customer_user_id = customer_user.id

        login_response = client.post(
            "/ecommerce/account/login",
            data={
                "email": "juan@test.com",
                "password": "TestPass#123",
            },
            follow_redirects=False,
        )
        assert login_response.status_code in (302, 303)
        assert "/ecommerce/account/dashboard" in login_response.headers.get(
            "Location", ""
        )

        dashboard_response = client.get("/ecommerce/account/dashboard")
        assert dashboard_response.status_code == 200
        assert b"Pedidos totales" in dashboard_response.data

        logout_response = client.post(
            "/ecommerce/account/logout",
            follow_redirects=False,
        )
        assert logout_response.status_code in (302, 303)

        protected_response = client.get(
            "/ecommerce/account/dashboard", follow_redirects=False
        )
        assert protected_response.status_code in (302, 303)

        with client.session_transaction() as session:
            assert session.get("ecommerce_customer_user_id") is None

        assert customer_user_id > 0


class TestCustomerCheckoutAndReviews:
    def test_authenticated_checkout_sets_customer_user_id(
        self,
        client,
        app,
        db_session,
        seed_basic_data,
    ):
        with app.app_context():
            customer = seed_basic_data["customer"]
            customer_user = CustomerUser(
                full_name=f"{customer.first_name} {customer.last_name}",
                email=customer.email,
                password_hash=hash_password("TestPass#123"),
                status=True,
            )
            db_session.add(customer_user)
            db_session.flush()
            customer.user_id = customer_user.id
            db_session.commit()
            customer_user_id = customer_user.id
            payment_method = seed_basic_data["payment_method"]
            product = seed_basic_data["product"]

        _login_customer_session(client, customer_user_id)
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )

        response = client.post(
            "/ecommerce/checkout",
            data={
                "delivery_mode": "pickup",
                "payment_method_id": str(payment_method.id),
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)
        assert "/ecommerce/checkout/success" in response.headers.get("Location", "")

        with app.app_context():
            created_order = Order.query.filter_by(source="ecommerce").first()
            assert created_order is not None
            assert created_order.customer_user_id == customer_user_id

    def test_review_requires_previous_purchase(
        self,
        client,
        app,
        db_session,
        seed_basic_data,
    ):
        with app.app_context():
            customer = seed_basic_data["customer"]
            customer_user = CustomerUser(
                full_name=f"{customer.first_name} {customer.last_name}",
                email=customer.email,
                password_hash=hash_password("TestPass#123"),
                status=True,
            )
            db_session.add(customer_user)
            db_session.flush()
            customer.user_id = customer_user.id

            product = seed_basic_data["product"]

            order = Order(
                customer_id=customer.id,
                customer_user_id=customer_user.id,
                status="entregado",
                total=product.price,
                source="ecommerce",
            )
            db_session.add(order)
            db_session.flush()
            db_session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=1,
                    price=product.price,
                )
            )
            db_session.commit()
            customer_user_id = customer_user.id

        _login_customer_session(client, customer_user_id)

        response = client.post(
            f"/ecommerce/account/reviews/product/{product.id}",
            data={
                "rating": "5",
                "review_text": "Excelente calidad",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)

        with app.app_context():
            review = ProductReview.query.filter_by(
                product_id=product.id,
                customer_user_id=customer_user_id,
            ).first()
            assert review is not None
            assert review.rating == 5
            assert review.review_text == "Excelente calidad"
