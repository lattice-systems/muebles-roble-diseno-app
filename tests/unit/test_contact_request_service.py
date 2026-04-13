"""Pruebas unitarias para ContactRequestService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.contact_requests.services import ContactRequestService
from app.models.contact_request import ContactRequest
from app.models.customer import Customer
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_inventory import ProductInventory


class TestContactRequestConversion:
    """Cubre la conversión de solicitudes a pedidos especiales."""

    def test_convert_to_special_order_creates_order_and_links_request(
        self, app, db_session, seed_basic_data
    ):
        """Convierte solicitud en cliente + producto especial + orden de cliente."""
        user = seed_basic_data["user"]

        contact_request = ContactRequest(
            full_name="Ana Lopez",
            email="ana.custom@test.com",
            phone="4775553322",
            subject="Comedor de parota 8 personas",
            message="Necesito una propuesta con medidas personalizadas.",
            request_type="custom_furniture",
            status="new",
            source="ecommerce",
        )
        db_session.add(contact_request)
        db_session.commit()

        order = ContactRequestService.convert_to_special_order(
            contact_request.id,
            form_data={
                "product_name": "Comedor parota especial",
                "quantity": "2",
                "unit_price": "3500.00",
                "estimated_delivery_date": (
                    date.today() + timedelta(days=15)
                ).isoformat(),
                "phone": "4775553322",
                "notes": "Incluir acabado mate y patas reforzadas.",
            },
            user_id=user.id,
        )

        assert order.id is not None
        assert order.is_special_request is True
        assert order.source == "manual"
        assert order.total == Decimal("7000.00")

        created_item = OrderItem.query.filter_by(order_id=order.id).first()
        assert created_item is not None

        special_product = db_session.get(Product, created_item.product_id)
        assert special_product is not None
        assert special_product.is_special_request is True
        assert special_product.name == "Comedor parota especial"

        product_inventory = ProductInventory.query.filter_by(
            product_id=special_product.id
        ).first()
        assert product_inventory is not None
        assert product_inventory.stock == 0

        refreshed_request = db_session.get(ContactRequest, contact_request.id)
        assert refreshed_request.converted_order_id == order.id
        assert refreshed_request.status == "completed"

        linked_customer = db_session.get(Customer, order.customer_id)
        assert linked_customer is not None
        assert linked_customer.email == "ana.custom@test.com"

    def test_convert_to_special_order_requires_phone_for_new_customer(
        self, app, db_session, seed_basic_data
    ):
        """Si no existe cliente previo, la conversión exige teléfono."""
        user = seed_basic_data["user"]

        contact_request = ContactRequest(
            full_name="Cliente Sin Telefono",
            email="sin.telefono@test.com",
            phone=None,
            subject="Closet personalizado",
            message="Necesito closet con medidas específicas para recámara principal.",
            request_type="custom_furniture",
            status="new",
            source="ecommerce",
        )
        db_session.add(contact_request)
        db_session.commit()

        with pytest.raises(ValueError, match="teléfono"):
            ContactRequestService.convert_to_special_order(
                contact_request.id,
                form_data={
                    "product_name": "Closet personalizado",
                    "quantity": "1",
                    "unit_price": "4200",
                    "estimated_delivery_date": (
                        date.today() + timedelta(days=20)
                    ).isoformat(),
                    "phone": "",
                    "notes": "",
                },
                user_id=user.id,
            )
