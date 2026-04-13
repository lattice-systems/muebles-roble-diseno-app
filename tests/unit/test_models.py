"""
Pruebas unitarias para modelos SQLAlchemy.

Valida serialización (to_dict), propiedades calculadas,
y constraints de la máquina de estados.
"""

from datetime import date, timedelta

from app.models.order import Order


class TestCustomerModel:
    """Tests para el modelo Customer."""

    def test_full_name(self, app, db_session, seed_basic_data):
        """Propiedad full_name concatena nombre y apellido."""
        customer = seed_basic_data["customer"]
        assert customer.full_name == "Juan Pérez"

    def test_to_dict_keys(self, app, db_session, seed_basic_data):
        """to_dict incluye todos los campos esperados."""
        customer = seed_basic_data["customer"]
        d = customer.to_dict()

        expected_keys = {
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "requires_freight",
            "zip_code",
            "state",
            "city",
            "street",
            "neighborhood",
            "exterior_number",
            "interior_number",
            "status",
            "created_at",
            "updated_at",
            "deactivated_at",
            "created_by",
            "updated_by",
            "deactivated_by",
        }
        assert expected_keys.issubset(set(d.keys()))

    def test_to_dict_values(self, app, db_session, seed_basic_data):
        """to_dict valores son correctos."""
        customer = seed_basic_data["customer"]
        d = customer.to_dict()

        assert d["first_name"] == "Juan"
        assert d["last_name"] == "Pérez"
        assert d["email"] == "juan@test.com"
        assert d["status"] is True


class TestProductModel:
    """Tests para el modelo Product."""

    def test_to_dict(self, app, db_session, seed_basic_data):
        """Serialización completa del producto."""
        product = seed_basic_data["product"]
        d = product.to_dict()

        assert d["id"] == product.id
        assert d["sku"] == "SILLA-001"
        assert d["name"] == "Silla Rústica"
        assert d["price"] == 1500.0
        assert d["status"] is True

    def test_product_has_inventory_relation(self, app, db_session, seed_basic_data):
        """Producto tiene relación con inventario."""
        product = seed_basic_data["product"]
        assert len(product.inventory_records) == 1
        assert product.inventory_records[0].stock == 10


class TestProductInventoryModel:
    """Tests para el modelo ProductInventory."""

    def test_to_dict(self, app, db_session, seed_basic_data):
        """Serialización del inventario."""
        inventory = seed_basic_data["inventory"]
        d = inventory.to_dict()

        assert d["product_id"] == seed_basic_data["product"].id
        assert d["stock"] == 10


class TestOrderModel:
    """Tests para el modelo Order y su máquina de estados."""

    def test_can_cancel_pendiente(self, app, db_session):
        """Orden pendiente puede cancelarse."""
        order = Order(status="pendiente")
        assert order.can_cancel() is True

    def test_cannot_cancel_entregado(self, app, db_session):
        """Orden entregada NO puede cancelarse."""
        order = Order(status="entregado")
        assert order.can_cancel() is False

    def test_can_send_to_production_pendiente(self, app, db_session):
        """Orden pendiente puede enviarse a producción."""
        order = Order(status="pendiente")
        assert order.can_send_to_production() is True

    def test_cannot_send_to_production_en_produccion(self, app, db_session):
        """Orden en producción NO puede enviarse de nuevo."""
        order = Order(status="en_produccion")
        assert order.can_send_to_production() is False

    def test_valid_statuses(self, app, db_session):
        """Constante VALID_STATUSES tiene todos los estados."""
        assert "pendiente" in Order.VALID_STATUSES
        assert "en_produccion" in Order.VALID_STATUSES
        assert "terminado" in Order.VALID_STATUSES
        assert "entregado" in Order.VALID_STATUSES
        assert "cancelado" in Order.VALID_STATUSES

    def test_status_transitions_map(self, app, db_session):
        """Mapa de transiciones es correcto."""
        transitions = Order.STATUS_TRANSITIONS

        # pendiente puede ir a 3 destinos
        assert "en_produccion" in transitions["pendiente"]
        assert "terminado" in transitions["pendiente"]
        assert "cancelado" in transitions["pendiente"]

        # entregado y cancelado no tienen transiciones
        assert transitions["entregado"] == ()
        assert transitions["cancelado"] == ()

    def test_to_dict(self, app, db_session, seed_basic_data):
        """Serialización de la orden."""
        from app.customer_orders.services import CustomerOrderService

        customer = seed_basic_data["customer"]
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]

        order = CustomerOrderService.create_order(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 1}],
            estimated_delivery_date=date.today() + timedelta(days=7),
            created_by_id=user.id,
        )

        d = order.to_dict()
        expected_keys = {
            "id",
            "customer_id",
            "order_date",
            "estimated_delivery_date",
            "status",
            "total",
            "payment_method_id",
            "notes",
            "source",
            "is_special_request",
            "customer_user_id",
            "created_by_id",
            "cancelled_at",
            "cancelled_by_id",
            "cancelled_reason",
            "sale_id",
        }
        assert expected_keys == set(d.keys())


class TestPaymentMethodModel:
    """Tests para el modelo PaymentMethod."""

    def test_to_dict(self, app, db_session, seed_basic_data):
        """Serialización del método de pago."""
        pm = seed_basic_data["payment_method"]
        d = pm.to_dict()

        assert d["name"] == "Efectivo"
        assert d["type"] == "cash"
        assert d["available_pos"] is True
        assert d["available_ecommerce"] is True


class TestRoleModel:
    """Tests para el modelo Role."""

    def test_to_dict(self, app, db_session, seed_basic_data):
        """Serialización del rol."""
        role = seed_basic_data["role"]
        d = role.to_dict()

        assert d["name"] == "admin"
        assert d["status"] is True


class TestUserModel:
    """Tests para el modelo User."""

    def test_to_dict(self, app, db_session, seed_basic_data):
        """Serialización del usuario."""
        user = seed_basic_data["user"]
        d = user.to_dict()

        assert d["full_name"] == "Test Admin"
        assert d["email"] == "admin@test.com"
        assert d["status"] is True
        assert "fs_uniquifier" in d
