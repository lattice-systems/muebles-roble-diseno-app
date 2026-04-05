"""
Pruebas unitarias para InventoryService.

Valida descuento de stock, stock insuficiente y producto sin inventario.
"""

import pytest

from app.models.product_inventory import ProductInventory
from app.shared.inventory_service import InventoryService


class TestDeductStock:
    """Tests para InventoryService.deduct_stock()."""

    def test_deduct_stock_success(self, app, db_session, seed_basic_data):
        """Descuenta correctamente del inventario."""
        product = seed_basic_data["product"]
        inventory = seed_basic_data["inventory"]
        original_stock = inventory.stock  # 10

        InventoryService.deduct_stock(
            product_id=product.id,
            quantity=3,
            product_name=product.name,
        )

        refreshed = ProductInventory.query.filter_by(product_id=product.id).first()
        assert refreshed.stock == original_stock - 3

    def test_deduct_stock_exact_amount(self, app, db_session, seed_basic_data):
        """Descuenta exactamente todo el stock disponible."""
        product = seed_basic_data["product"]
        inventory = seed_basic_data["inventory"]

        InventoryService.deduct_stock(
            product_id=product.id,
            quantity=inventory.stock,
            product_name=product.name,
        )

        refreshed = ProductInventory.query.filter_by(product_id=product.id).first()
        assert refreshed.stock == 0

    def test_deduct_stock_insufficient_raises(self, app, db_session, seed_basic_data):
        """Lanza ValueError si el stock es insuficiente."""
        product = seed_basic_data["product"]

        with pytest.raises(ValueError, match="Stock insuficiente"):
            InventoryService.deduct_stock(
                product_id=product.id,
                quantity=999,
                product_name=product.name,
            )

    def test_deduct_stock_no_inventory_raises(self, app, db_session, seed_basic_data):
        """Lanza ValueError si el producto no tiene registro de inventario."""
        with pytest.raises(ValueError, match="no tiene registro de inventario"):
            InventoryService.deduct_stock(
                product_id=99999,
                quantity=1,
                product_name="Producto Fantasma",
            )

    def test_deduct_stock_uses_product_id_as_label(
        self, app, db_session, seed_basic_data
    ):
        """Cuando no se pasa product_name, usa ID como label en el error."""
        with pytest.raises(ValueError, match="ID 99999"):
            InventoryService.deduct_stock(
                product_id=99999,
                quantity=1,
            )
