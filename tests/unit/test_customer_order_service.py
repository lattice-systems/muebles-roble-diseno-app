"""
Pruebas unitarias para CustomerOrderService.

Cubre: creación de órdenes, cancelación, máquina de estados,
creación desde ecommerce y validaciones.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.customer_orders.services import CustomerOrderService


class TestCreateOrder:
    """Tests para CustomerOrderService.create_order()."""

    def test_create_success(self, app, db_session, seed_basic_data):
        """Crea orden con items y auditoría."""
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]

        order = CustomerOrderService.create_order(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 2}],
            estimated_delivery_date=date.today() + timedelta(days=7),
            notes="Test order",
            source="manual",
            created_by_id=user.id,
        )

        assert order.id is not None
        assert order.status == "pendiente"
        assert order.source == "manual"
        assert len(order.items) == 1
        assert order.total == Decimal(str(product.price)) * 2

    def test_create_empty_items_raises(self, app, db_session, seed_basic_data):
        """Sin productos lanza ValueError."""
        customer = seed_basic_data["customer"]

        with pytest.raises(ValueError, match="al menos un producto"):
            CustomerOrderService.create_order(
                customer_id=customer.id,
                items=[],
                estimated_delivery_date=date.today() + timedelta(days=7),
            )

    def test_create_invalid_customer_raises(self, app, db_session, seed_basic_data):
        """Cliente inexistente lanza ValueError."""
        product = seed_basic_data["product"]

        with pytest.raises(ValueError, match="Cliente no encontrado"):
            CustomerOrderService.create_order(
                customer_id=99999,
                items=[{"product_id": product.id, "quantity": 1}],
                estimated_delivery_date=date.today() + timedelta(days=7),
            )

    def test_create_invalid_product_raises(self, app, db_session, seed_basic_data):
        """Producto inexistente lanza ValueError."""
        customer = seed_basic_data["customer"]

        with pytest.raises(ValueError, match="no encontrado"):
            CustomerOrderService.create_order(
                customer_id=customer.id,
                items=[{"product_id": 99999, "quantity": 1}],
                estimated_delivery_date=date.today() + timedelta(days=7),
            )

    def test_create_zero_quantity_raises(self, app, db_session, seed_basic_data):
        """Cantidad 0 lanza ValueError."""
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]

        with pytest.raises(ValueError, match="mayor a 0"):
            CustomerOrderService.create_order(
                customer_id=customer.id,
                items=[{"product_id": product.id, "quantity": 0}],
                estimated_delivery_date=date.today() + timedelta(days=7),
            )

    def test_create_no_delivery_date_raises(self, app, db_session, seed_basic_data):
        """Sin fecha de entrega lanza ValueError."""
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]

        with pytest.raises(ValueError, match="fecha estimada"):
            CustomerOrderService.create_order(
                customer_id=customer.id,
                items=[{"product_id": product.id, "quantity": 1}],
                estimated_delivery_date=None,
            )


class TestCancelOrder:
    """Tests para CustomerOrderService.cancel_order()."""

    def _create_test_order(self, seed_basic_data):
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]
        return CustomerOrderService.create_order(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 1}],
            estimated_delivery_date=date.today() + timedelta(days=7),
            created_by_id=user.id,
        )

    def test_cancel_success(self, app, db_session, seed_basic_data):
        """Cancela orden en estado pendiente."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        cancelled = CustomerOrderService.cancel_order(
            order_id=order.id,
            user_id=user.id,
            reason="Ya no lo necesito",
        )

        assert cancelled.status == "cancelado"
        assert cancelled.cancelled_reason == "Ya no lo necesito"
        assert cancelled.cancelled_by_id == user.id

    def test_cancel_no_reason_raises(self, app, db_session, seed_basic_data):
        """Sin razón lanza ValueError."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        with pytest.raises(ValueError, match="motivo"):
            CustomerOrderService.cancel_order(
                order_id=order.id,
                user_id=user.id,
                reason="",
            )

    def test_cancel_already_cancelled_raises(self, app, db_session, seed_basic_data):
        """Cancelar orden ya cancelada lanza ValueError."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        CustomerOrderService.cancel_order(
            order_id=order.id,
            user_id=user.id,
            reason="Primera cancelación",
        )

        with pytest.raises(ValueError, match="no puede cancelarse"):
            CustomerOrderService.cancel_order(
                order_id=order.id,
                user_id=user.id,
                reason="Segunda cancelación",
            )


class TestStatusTransitions:
    """Tests para la máquina de estados de Order."""

    def _create_test_order(self, seed_basic_data):
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]
        return CustomerOrderService.create_order(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 1}],
            estimated_delivery_date=date.today() + timedelta(days=7),
            created_by_id=user.id,
        )

    def test_valid_transition_pendiente_to_terminado(
        self, app, db_session, seed_basic_data
    ):
        """Transición válida: pendiente → terminado."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        updated = CustomerOrderService.update_status(
            order_id=order.id,
            new_status="terminado",
            user_id=user.id,
        )
        assert updated.status == "terminado"

    def test_valid_transition_terminado_to_entregado(
        self, app, db_session, seed_basic_data
    ):
        """Transición válida: terminado → entregado."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        CustomerOrderService.update_status(
            order_id=order.id, new_status="terminado", user_id=user.id
        )
        updated = CustomerOrderService.update_status(
            order_id=order.id, new_status="entregado", user_id=user.id
        )
        assert updated.status == "entregado"

    def test_invalid_transition_raises(self, app, db_session, seed_basic_data):
        """Transición inválida lanza ValueError."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        with pytest.raises(ValueError, match="No se puede cambiar"):
            CustomerOrderService.update_status(
                order_id=order.id,
                new_status="entregado",  # pendiente → entregado no es válido
                user_id=user.id,
            )

    def test_idempotent_same_status(self, app, db_session, seed_basic_data):
        """Aplicar el mismo estado no falla (idempotencia)."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        updated = CustomerOrderService.update_status(
            order_id=order.id, new_status="pendiente", user_id=user.id
        )
        assert updated.status == "pendiente"

    def test_invalid_status_value_raises(self, app, db_session, seed_basic_data):
        """Estado no válido lanza ValueError."""
        order = self._create_test_order(seed_basic_data)
        user = seed_basic_data["user"]

        with pytest.raises(ValueError, match="inválido"):
            CustomerOrderService.update_status(
                order_id=order.id,
                new_status="estado_inventado",
                user_id=user.id,
            )


class TestSendToProduction:
    """Tests para CustomerOrderService.send_to_production()."""

    def test_send_to_production_leaves_order_in_production_state(
        self, app, db_session, seed_basic_data
    ):
        """Enviar una orden a producción no debe cerrarla directamente."""
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]

        order = CustomerOrderService.create_order(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 1}],
            estimated_delivery_date=date.today() + timedelta(days=7),
            created_by_id=user.id,
        )

        production_orders = CustomerOrderService.send_to_production(
            order_id=order.id,
            user_id=user.id,
        )

        assert production_orders == []
        assert order.status == "en_produccion"


class TestCreateFromEcommerce:
    """Tests para CustomerOrderService.create_from_ecommerce()."""

    def test_create_from_ecommerce(self, app, db_session, seed_basic_data):
        """Crea orden desde checkout ecommerce."""
        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]

        order = CustomerOrderService.create_from_ecommerce(
            customer_id=customer.id,
            cart_items=[
                {"product_id": product.id, "quantity": 2, "price": float(product.price)}
            ],
            payment_method_id=pm.id,
            total=Decimal(str(float(product.price) * 2)),
            notes="Pedido de prueba ecommerce",
        )

        assert order.id is not None
        assert order.source == "ecommerce"
        assert order.status == "pendiente"
        assert order.created_by_id is None  # ecommerce no tiene usuario
        assert len(order.items) == 1
