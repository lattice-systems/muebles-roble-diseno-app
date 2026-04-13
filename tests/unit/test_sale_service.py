"""
Pruebas unitarias para SaleService y SaleItemService.

Cubre: apertura de venta POS, checkout, manejo de items,
validaciones de stock y monto insuficiente.
"""

import pytest

from app.exceptions import NotFoundError
from app.models.product_inventory import ProductInventory
from app.models.sale import Sale
from app.sales.services import SaleItemService, SaleService


class TestOpenSale:
    """Tests para SaleService.open_sale()."""

    def test_open_sale_creates_active(self, app, db_session, seed_basic_data):
        """Crea una venta activa con auditoría."""
        user = seed_basic_data["user"]
        sale = SaleService.open_sale(employee_id=user.id)

        assert sale.id is not None
        assert sale.active is True
        assert sale.total == 0
        assert sale.id_employee == user.id

    def test_open_sale_with_customer(self, app, db_session, seed_basic_data):
        """Crea venta con cliente asignado."""
        user = seed_basic_data["user"]
        customer = seed_basic_data["customer"]
        sale = SaleService.open_sale(employee_id=user.id, customer_id=customer.id)
        assert sale.id_customer == customer.id


class TestGetActiveSale:
    """Tests para SaleService.get_active_sale()."""

    def test_found(self, app, db_session, seed_basic_data):
        """Retorna venta activa existente."""
        user = seed_basic_data["user"]
        sale = SaleService.open_sale(employee_id=user.id)
        found = SaleService.get_active_sale(sale.id)
        assert found.id == sale.id

    def test_not_found_raises(self, app, db_session, seed_basic_data):
        """Lanza NotFoundError si no existe."""
        with pytest.raises(NotFoundError):
            SaleService.get_active_sale(99999)


class TestSearchCustomers:
    """Tests para SaleService.search_customers()."""

    def test_search_by_name(self, app, db_session, seed_basic_data):
        """Busca clientes por nombre."""
        results = SaleService.search_customers("Juan")
        assert len(results) >= 1
        assert any("Juan" in r.get("first_name", "") for r in results)

    def test_search_too_short(self, app, db_session, seed_basic_data):
        """Búsqueda menor a 2 caracteres retorna vacío."""
        results = SaleService.search_customers("J")
        assert results == []

    def test_search_empty(self, app, db_session, seed_basic_data):
        """Búsqueda vacía retorna vacío."""
        results = SaleService.search_customers("")
        assert results == []


class TestProductCatalogFiltering:
    """Tests para filtros de productos del POS."""

    def test_get_products_excludes_special_request_products(
        self, app, db_session, seed_basic_data
    ):
        """El catálogo POS no debe incluir productos marcados como especiales."""
        from app.models.furniture_type import FurnitureType
        from app.models.product import Product
        from app.models.product_inventory import ProductInventory

        furniture_type = FurnitureType(
            title="Especial POS",
            subtitle="No comercial",
            image_url="https://example.com/especial-pos.jpg",
            slug="especial-pos",
            status=True,
        )
        db_session.add(furniture_type)
        db_session.flush()

        special_product = Product(
            sku="POS-ESP-001",
            name="Producto especial POS",
            furniture_type_id=furniture_type.id,
            description="No debe aparecer en POS",
            price=1800.0,
            status=True,
            is_special_request=True,
        )
        db_session.add(special_product)
        db_session.flush()

        db_session.add(ProductInventory(product_id=special_product.id, stock=4))
        db_session.commit()

        pagination = SaleService.get_products(page=1, per_page=50)
        product_ids = {product.id for product in pagination.items}
        assert special_product.id not in product_ids


class TestCreateCustomer:
    """Tests para SaleService.create_customer()."""

    def test_create_success(self, app, db_session, seed_basic_data):
        """Crea cliente con datos válidos."""
        data = {
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana@test.com",
            "phone": "4771112233",
        }
        customer = SaleService.create_customer(data)
        assert customer.id is not None
        assert customer.first_name == "Ana"

    def test_create_missing_fields_raises(self, app, db_session, seed_basic_data):
        """Campos faltantes lanzan ValueError."""
        with pytest.raises(ValueError, match="obligatorios"):
            SaleService.create_customer({"first_name": "Solo"})

    def test_create_duplicate_email_raises(self, app, db_session, seed_basic_data):
        """Email duplicado lanza ValueError."""
        with pytest.raises(ValueError, match="ya está registrado"):
            SaleService.create_customer(
                {
                    "first_name": "Dup",
                    "last_name": "Test",
                    "email": "juan@test.com",  # ya existe en seed
                    "phone": "123",
                }
            )


class TestCheckoutSale:
    """Tests para SaleService.checkout_sale()."""

    def test_checkout_empty_cart_raises(self, app, db_session, seed_basic_data):
        """Carrito vacío lanza ValueError."""
        user = seed_basic_data["user"]
        pm = seed_basic_data["payment_method"]
        sale = SaleService.open_sale(employee_id=user.id)

        with pytest.raises(ValueError, match="vacío"):
            SaleService.checkout_sale(
                sale_id=sale.id,
                amount_given=1000.0,
                payment_method_id=pm.id,
            )

    def test_checkout_insufficient_amount_raises(
        self, app, db_session, seed_basic_data
    ):
        """Monto insuficiente lanza ValueError."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]

        sale = SaleService.open_sale(employee_id=user.id)
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=1
        )

        with pytest.raises(ValueError, match="insuficiente"):
            SaleService.checkout_sale(
                sale_id=sale.id,
                amount_given=1.0,
                payment_method_id=pm.id,
            )

    def test_checkout_success(self, app, db_session, seed_basic_data):
        """Checkout exitoso: desactiva venta, descuenta stock, registra pago."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]
        original_stock = seed_basic_data["inventory"].stock

        sale = SaleService.open_sale(employee_id=user.id)
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=2
        )

        result = SaleService.checkout_sale(
            sale_id=sale.id,
            amount_given=5000.0,
            payment_method_id=pm.id,
        )

        assert result["success"] is True
        assert result["change"] >= 0

        # Venta desactivada
        refreshed_sale = Sale.query.get(sale.id)
        assert refreshed_sale.active is False

        # Stock descontado
        inv = ProductInventory.query.filter_by(product_id=product.id).first()
        assert inv.stock == original_stock - 2


class TestSaleItemService:
    """Tests para SaleItemService (manejo de carrito POS en BD)."""

    def test_add_item(self, app, db_session, seed_basic_data):
        """Agrega item a la venta."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]

        sale = SaleService.open_sale(employee_id=user.id)
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=2
        )

        items = SaleItemService.get_cart_items(sale.id)
        assert len(items) == 1
        assert items[0]["quantity"] == 2

    def test_add_item_stacks_quantity(self, app, db_session, seed_basic_data):
        """Agregar el mismo producto suma cantidades."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]

        sale = SaleService.open_sale(employee_id=user.id)
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=2
        )
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=3
        )

        items = SaleItemService.get_cart_items(sale.id)
        assert len(items) == 1
        assert items[0]["quantity"] == 5

    def test_add_item_exceeds_stock_raises(self, app, db_session, seed_basic_data):
        """Agregar más stock del disponible lanza ValueError."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]

        sale = SaleService.open_sale(employee_id=user.id)
        with pytest.raises(ValueError, match="Stock insuficiente"):
            SaleItemService.add_item_to_sale(
                sale_id=sale.id, product_id=product.id, quantity=999
            )

    def test_update_item_quantity(self, app, db_session, seed_basic_data):
        """Actualizar cantidad de un item."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]

        sale = SaleService.open_sale(employee_id=user.id)
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=2
        )

        items = SaleItemService.get_cart_items(sale.id)
        SaleItemService.update_item_quantity(
            sale_id=sale.id, item_id=items[0]["id"], quantity=5
        )

        updated_items = SaleItemService.get_cart_items(sale.id)
        assert updated_items[0]["quantity"] == 5

    def test_remove_item(self, app, db_session, seed_basic_data):
        """Eliminar item de la venta."""
        user = seed_basic_data["user"]
        product = seed_basic_data["product"]

        sale = SaleService.open_sale(employee_id=user.id)
        SaleItemService.add_item_to_sale(
            sale_id=sale.id, product_id=product.id, quantity=2
        )

        items = SaleItemService.get_cart_items(sale.id)
        SaleItemService.remove_item_from_sale(sale_id=sale.id, item_id=items[0]["id"])

        assert SaleItemService.get_cart_items(sale.id) == []
