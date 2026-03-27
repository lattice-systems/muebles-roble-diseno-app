"""
Servicios de lógica de negocio para el módulo de ventas POS.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.payment_method import PaymentMethod
from app.models.product import Product
from app.models.product_inventory import ProductInventory
from app.models.sale import Sale
from app.models.sale_item import SaleItem


class SaleService:
    """Servicio para operaciones de negocio relacionadas con ventas POS."""

    @staticmethod
    def open_sale(
        employee_id: int,
        customer_id: Optional[int] = None,
    ) -> Sale:
        """
        Abre una nueva cabecera de venta en estado activo.

        Crea el registro en `sales` y registra la auditoría en `audit_log`
        (doble capa: Python + trigger MySQL).

        Args:
            employee_id: ID del empleado (usuario logueado) que abre la venta.
            customer_id: ID del cliente (opcional).

        Returns:
            Sale: Objeto de venta creado.
        """
        sale = Sale(
            id_employee=employee_id,
            id_customer=customer_id if customer_id else None,
            active=True,
            total=0,
            sale_date=datetime.now(timezone.utc),
        )
        db.session.add(sale)
        db.session.flush()  # obtiene el ID antes del commit

        # Auditoría desde Python (complementa el trigger MySQL)
        audit = AuditLog(
            table_name="sales",
            action="INSERT",
            user_id=employee_id,
            timestamp=datetime.now(timezone.utc),
            previous_data=None,
            new_data=sale.to_dict(),
        )
        db.session.add(audit)
        db.session.commit()

        return sale

    @staticmethod
    def get_active_sale(sale_id: int) -> Sale:
        """
        Obtiene una venta activa por ID.

        Args:
            sale_id: ID de la venta.

        Returns:
            Sale: Objeto de venta activa.

        Raises:
            NotFoundError: Si la venta no existe o no está activa.
        """
        sale = Sale.query.filter_by(id=sale_id, active=True).first()
        if not sale:
            raise NotFoundError(f"No se encontró una venta activa con ID {sale_id}")
        return sale

    @staticmethod
    def search_customers(q: str, limit: int = 10) -> list[dict]:
        """
        Busca clientes activos por nombre o email para el autocompletar.

        Args:
            q: Término de búsqueda (mínimo 2 caracteres).
            limit: Número máximo de resultados.

        Returns:
            list[dict]: Lista de clientes serializados.
        """
        if not q or len(q.strip()) < 2:
            return []

        search = f"%{q.strip()}%"
        customers = (
            Customer.query.filter(
                Customer.status == True,  # noqa: E712
                or_(
                    Customer.full_name.ilike(search),
                    Customer.email.ilike(search),
                ),
            )
            .limit(limit)
            .all()
        )
        return [c.to_dict() for c in customers]

    @staticmethod
    def create_customer(data: dict) -> Customer:
        """
        Crea un nuevo cliente.
        """
        existing = Customer.query.filter_by(email=data.get("email")).first()
        if existing:
            raise ValueError("El correo electrónico ya está registrado.")

        customer = Customer(
            full_name=data.get("full_name"),
            email=data.get("email"),
            phone=data.get("phone", ""),
            address=data.get("address", ""),
            status=True,
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def get_products(
        search_term: str = "",
        page: int = 1,
        per_page: int = 8,
    ):
        """
        Lista productos activos paginados para la cuadrícula del POS.

        Args:
            search_term: Filtro por nombre o SKU.
            page: Número de página.
            per_page: Productos por página.

        Returns:
            Pagination: Objeto de paginación de SQLAlchemy.
        """
        query = Product.query.options(
            selectinload(Product.inventory_records)
        ).filter_by(status=True)

        if search_term:
            search = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search),
                    Product.sku.ilike(search),
                )
            )

        return query.order_by(Product.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_payment_methods():
        return PaymentMethod.query.filter_by(status=True, available_pos=True).all()

    @staticmethod
    def checkout_sale(
        sale_id: int, amount_given: float, payment_method_id: int
    ) -> dict:
        sale = SaleService.get_active_sale(sale_id)
        if not sale.items:
            raise ValueError("El carrito está vacío no hay nada que cobrar.")

        calculated_total = sum(item.price * item.quantity for item in sale.items)
        if sale.total != calculated_total:
            sale.total = calculated_total
            db.session.commit()

        if amount_given < float(sale.total):
            raise ValueError(
                f"Monto insuficiente. Faltan ${(float(sale.total) - amount_given):,.2f}"
            )

        # Reducir stock (RF-VENT-03 / 05)
        for item in sale.items:
            inv = (
                item.product.inventory_records[0]
                if item.product.inventory_records
                else None
            )
            # fallback local query if lazy
            if not inv:
                from app.models.product_inventory import ProductInventory

                inv = ProductInventory.query.filter_by(
                    product_id=item.product_id
                ).first()
            if inv:
                inv.stock -= item.quantity
                if inv.stock < 0:
                    db.session.rollback()
                    raise ValueError(
                        f"Inventario negativo detectado para el artículo {item.product.name}"
                    )

        sale.payment_method_id = payment_method_id
        sale.active = False

        payment = Payment(payment_type="SALE", id_sale=sale.id, amount=amount_given)
        db.session.add(payment)

        change = float(amount_given - float(sale.total))
        db.session.commit()

        return {"success": True, "change": change, "total": float(sale.total)}


class SaleItemService:
    """Servicio para gestionar los detalles de venta (carrito) del POS."""

    @staticmethod
    def _calculate_sale_total(sale_id: int) -> Decimal:
        items = SaleItem.query.filter_by(sale_id=sale_id).all()
        return sum((item.price * item.quantity for item in items), Decimal("0"))

    @staticmethod
    def get_cart_items(sale_id: int) -> list[dict]:
        items = (
            SaleItem.query.filter_by(sale_id=sale_id).order_by(SaleItem.id.asc()).all()
        )
        return [
            {
                "id": i.id,
                "product_id": i.product_id,
                "name": i.product.name,
                "sku": i.product.sku,
                "price": float(i.price),
                "quantity": i.quantity,
                "subtotal": float(i.price * i.quantity),
            }
            for i in items
        ]

    @staticmethod
    def add_item_to_sale(sale_id: int, product_id: int, quantity: int = 1) -> None:
        sale = SaleService.get_active_sale(sale_id)
        product = Product.query.filter_by(id=product_id, status=True).first()
        if not product:
            raise NotFoundError("El producto no existe o está inactivo.")

        # Verificar stock disponible
        inventory = ProductInventory.query.filter_by(product_id=product.id).first()
        available_stock = inventory.stock if inventory else 0

        existing_item = SaleItem.query.filter_by(
            sale_id=sale.id, product_id=product.id
        ).first()

        current_qty = existing_item.quantity if existing_item else 0
        new_qty = current_qty + quantity

        if new_qty > available_stock:
            raise ValueError(
                f"Stock insuficiente para '{product.name}'. "
                f"Disponible: {available_stock}, solicitado: {new_qty}."
            )

        if existing_item:
            existing_item.quantity = new_qty
        else:
            new_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                price=product.price,
            )
            db.session.add(new_item)

        sale.total = SaleItemService._calculate_sale_total(sale.id)
        db.session.commit()

    @staticmethod
    def update_item_quantity(sale_id: int, item_id: int, quantity: int) -> None:
        sale = SaleService.get_active_sale(sale_id)
        if quantity < 1:
            raise ValueError("La cantidad debe ser mayor a 0.")

        item = SaleItem.query.filter_by(id=item_id, sale_id=sale.id).first()
        if not item:
            raise NotFoundError("Detalle no encontrado en esta venta.")

        # Verificar stock disponible
        inventory = ProductInventory.query.filter_by(product_id=item.product_id).first()
        available_stock = inventory.stock if inventory else 0

        if quantity > available_stock:
            product = Product.query.get(item.product_id)
            raise ValueError(
                f"Stock insuficiente para '{product.name}'. "
                f"Disponible: {available_stock}, solicitado: {quantity}."
            )

        item.quantity = quantity
        sale.total = SaleItemService._calculate_sale_total(sale.id)
        db.session.commit()

    @staticmethod
    def remove_item_from_sale(sale_id: int, item_id: int) -> None:
        sale = SaleService.get_active_sale(sale_id)
        item = SaleItem.query.filter_by(id=item_id, sale_id=sale.id).first()
        if not item:
            raise NotFoundError("Detalle no encontrado en esta venta.")

        db.session.delete(item)
        sale.total = SaleItemService._calculate_sale_total(sale.id)
        db.session.commit()
