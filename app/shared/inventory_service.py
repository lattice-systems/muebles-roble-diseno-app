"""
Servicio compartido para operaciones de inventario.

Centraliza la lógica de descuento de stock que se repite
en el módulo de ventas POS y en el checkout de ecommerce.
"""

from app.models.product_inventory import ProductInventory


class InventoryService:
    """Operaciones reutilizables sobre inventario de productos."""

    @staticmethod
    def deduct_stock(product_id: int, quantity: int, product_name: str = "") -> None:
        """
        Descuenta *quantity* unidades del stock de un producto.

        Args:
            product_id: ID del producto en ``products``.
            quantity: Cantidad a descontar (debe ser > 0).
            product_name: Nombre legible para mensajes de error.

        Raises:
            ValueError: Si no existe inventario o el stock resultante es negativo.
        """
        label = product_name or f"ID {product_id}"

        inventory = ProductInventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            raise ValueError(f"El producto '{label}' no tiene registro de inventario.")

        inventory.stock -= quantity
        if inventory.stock < 0:
            raise ValueError(
                f"Stock insuficiente para '{label}'. "
                f"Disponible: {inventory.stock + quantity}, solicitado: {quantity}."
            )
