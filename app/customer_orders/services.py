"""
Servicios de lógica de negocio para el módulo de Órdenes de Cliente (HU-14).
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.production_order import ProductionOrder


class CustomerOrderService:
    """Servicio para la gestión de órdenes de cliente (HU-14)."""

    # ------------------------------------------------------------------ #
    #  Consultas                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_orders(
        *,
        customer_q: str = "",
        status: str = "",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        per_page: int = 15,
    ):
        """
        Lista paginada de órdenes con filtros.

        Returns:
            Pagination: Objeto de paginación de SQLAlchemy.
        """
        query = Order.query.options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.created_by),
        )

        if status:
            query = query.filter(Order.status == status)

        if date_from:
            query = query.filter(Order.order_date >= date_from)
        if date_to:
            query = query.filter(Order.order_date <= date_to)

        if customer_q:
            search = f"%{customer_q.strip()}%"
            query = query.join(Order.customer).filter(
                or_(
                    Customer.first_name.ilike(search),
                    Customer.last_name.ilike(search),
                    Customer.email.ilike(search),
                )
            )

        return query.order_by(Order.order_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_order_by_id(order_id: int) -> Order:
        """Retorna una orden o lanza 404."""
        return Order.query.options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.created_by),
            selectinload(Order.cancelled_by),
            selectinload(Order.production_orders),
        ).get_or_404(order_id)

    @staticmethod
    def get_order_history(order_id: int) -> list[dict]:
        """Retorna el historial de auditoría de una orden."""
        logs = (
            AuditLog.query.filter_by(table_name="orders")
            .order_by(AuditLog.timestamp.asc())
            .all()
        )
        # Filtrar por order_id en new_data o previous_data
        result = []
        for log in logs:
            nd = log.new_data or {}
            pd = log.previous_data or {}
            if str(nd.get("id")) == str(order_id) or str(pd.get("id")) == str(order_id):
                result.append(
                    {
                        "timestamp": (
                            log.timestamp.isoformat() if log.timestamp else None
                        ),
                        "action": log.action,
                        "user_id": log.user_id,
                        "previous_data": pd,
                        "new_data": nd,
                    }
                )
        return result

    # ------------------------------------------------------------------ #
    #  Búsquedas para autocompletado                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def search_customers(q: str, limit: int = 10) -> list[dict]:
        """Busca clientes activos por nombre/email para el autocompletado."""
        if not q or len(q.strip()) < 2:
            return []
        search = f"%{q.strip()}%"
        customers = (
            Customer.query.filter(
                Customer.status == True,  # noqa: E712
                or_(
                    Customer.first_name.ilike(search),
                    Customer.last_name.ilike(search),
                    Customer.email.ilike(search),
                ),
            )
            .limit(limit)
            .all()
        )
        return [c.to_dict() for c in customers]

    @staticmethod
    def get_products(search_term: str = "", page: int = 1, per_page: int = 8):
        """Productos activos paginados para el selector de la orden."""
        query = Product.query.options(
            selectinload(Product.inventory_records)
        ).filter_by(status=True)

        if search_term:
            s = f"%{search_term.strip()}%"
            query = query.filter(or_(Product.name.ilike(s), Product.sku.ilike(s)))

        return query.order_by(Product.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    # ------------------------------------------------------------------ #
    #  Creación                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_order(
        *,
        customer_id: int,
        items: list[dict],
        estimated_delivery_date: date,
        payment_method_id: Optional[int] = None,
        notes: str = "",
        source: str = "manual",
        created_by_id: Optional[int] = None,
    ) -> Order:
        """
        Crea una orden de cliente con sus items.

        Args:
            customer_id: ID del cliente.
            items: Lista de dicts {'product_id': int, 'quantity': int}.
            estimated_delivery_date: Fecha estimada de entrega (obligatoria).
            payment_method_id: Método de pago (opcional).
            notes: Notas del pedido.
            source: 'pos' | 'ecommerce' | 'manual'.
            created_by_id: ID del usuario que crea la orden.

        Returns:
            Order: Orden creada.

        Raises:
            ValueError: Si el cliente, algún producto o la cantidad son inválidos.
        """
        if not items:
            raise ValueError("La orden debe contener al menos un producto.")

        customer = Customer.query.filter_by(id=customer_id, status=True).first()
        if not customer:
            raise ValueError("Cliente no encontrado o inactivo.")

        if not estimated_delivery_date:
            raise ValueError("La fecha estimada de entrega es obligatoria.")

        if source not in Order.VALID_SOURCES:
            source = "manual"

        total = Decimal("0")
        order_items = []

        for item_data in items:
            product_id = int(item_data.get("product_id", 0))
            quantity = int(item_data.get("quantity", 0))

            if quantity < 1:
                raise ValueError("La cantidad debe ser mayor a 0.")

            product = Product.query.filter_by(id=product_id, status=True).first()
            if not product:
                raise ValueError(
                    f"Producto con ID {product_id} no encontrado o inactivo."
                )

            subtotal = product.price * quantity
            total += subtotal

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price,
                )
            )

        order = Order(
            customer_id=customer_id,
            order_date=datetime.now(),
            estimated_delivery_date=estimated_delivery_date,
            status="pendiente",
            total=total,
            payment_method_id=payment_method_id,
            notes=notes.strip() if notes else None,
            source=source,
            created_by_id=created_by_id,
        )
        db.session.add(order)
        db.session.flush()

        for item in order_items:
            item.order_id = order.id
            db.session.add(item)

        # Auditoría
        db.session.add(
            AuditLog(
                table_name="orders",
                action="INSERT",
                user_id=created_by_id,
                timestamp=datetime.now(),
                previous_data=None,
                new_data=order.to_dict(),
            )
        )

        db.session.commit()
        return order

    # ------------------------------------------------------------------ #
    #  Cancelación                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def cancel_order(
        order_id: int,
        user_id: int,
        reason: str,
    ) -> Order:
        """
        Cancela una orden si está en estado 'pendiente'.

        Raises:
            ValueError: Si la orden no puede cancelarse.
        """
        order = Order.query.get_or_404(order_id)

        if not order.can_cancel():
            raise ValueError(
                f"La orden #{order.id} no puede cancelarse porque ya está en estado "
                f"'{order.status}'. Solo se puede cancelar en estado 'pendiente'."
            )

        if not reason or not reason.strip():
            raise ValueError("Debe proporcionar un motivo de cancelación.")

        prev_data = order.to_dict()
        order.status = "cancelado"
        order.cancelled_at = datetime.now()
        order.cancelled_by_id = user_id
        order.cancelled_reason = reason.strip()

        db.session.add(
            AuditLog(
                table_name="orders",
                action="UPDATE",
                user_id=user_id,
                timestamp=datetime.now(),
                previous_data=prev_data,
                new_data=order.to_dict(),
            )
        )

        db.session.commit()
        return order

    # ------------------------------------------------------------------ #
    #  Enviar a Producción                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def send_to_production(
        order_id: int,
        user_id: int,
    ) -> list[ProductionOrder]:
        """
        Genera órdenes de producción (una por OrderItem) y avanza el estado
        de la orden de cliente a 'en_produccion'.

        - Crea una ProductionOrder por cada item con la cantidad completa.
        - Inicializa consumo planificado de materiales con la receta BOM.
        - Siempre marca la orden como 'en_produccion'.
        - El módulo de producción se encarga de marcar la orden como
          'terminado' cuando todas las órdenes de producción se completen.

        Returns:
            Lista de ProductionOrder creadas.

        Raises:
            ValueError: Si la orden no puede enviarse a producción.
        """
        order = Order.query.options(
            selectinload(Order.items).selectinload(OrderItem.product)
        ).get_or_404(order_id)

        if not order.can_send_to_production():
            raise ValueError(
                f"La orden #{order.id} no puede enviarse a producción porque ya está "
                f"en estado '{order.status}'."
            )

        if not order.items:
            raise ValueError("La orden no tiene productos.")

        prev_data = order.to_dict()
        production_orders = []

        # Import local para evitar ciclos entre módulos
        from app.production.services import ProductionService

        for item in order.items:
            # Crear orden de producción por la cantidad total del item.
            # El módulo de producción se encarga de consumir materiales
            # y actualizar inventario al marcar la orden como terminada.
            prod_order = ProductionOrder(
                product_id=item.product_id,
                quantity=int(item.quantity),
                status="pendiente",
                scheduled_date=order.estimated_delivery_date or date.today(),
                customer_order_id=order.id,
                created_by=user_id,
                updated_by=user_id,
            )
            db.session.add(prod_order)
            db.session.flush()

            ProductionService.initialize_material_plan_for_order(prod_order)
            production_orders.append(prod_order)

        # Siempre poner en producción; el módulo de producción se encargará
        # de marcar la orden como "terminado" cuando todas las órdenes de
        # producción se completen (vía _sync_customer_order_status).
        order.status = "en_produccion"

        db.session.flush()

        db.session.add(
            AuditLog(
                table_name="orders",
                action="UPDATE",
                user_id=user_id,
                timestamp=datetime.now(),
                previous_data=prev_data,
                new_data=order.to_dict(),
            )
        )

        db.session.commit()
        return production_orders

    # ------------------------------------------------------------------ #
    #  Actualizar estado manualmente                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def update_status(
        order_id: int,
        new_status: str,
        user_id: int,
    ) -> Order:
        """
        Actualiza el estado de una orden respetando las transiciones válidas.

        Raises:
            ValueError: Si la transición no está permitida.
        """
        if new_status not in Order.VALID_STATUSES:
            raise ValueError(f"Estado inválido: {new_status}")

        order = Order.query.options(
            selectinload(Order.customer),
            selectinload(Order.production_orders),
        ).get_or_404(order_id)

        # Idempotencia: si ya tiene el estado destino, no hacer nada
        if order.status == new_status:
            return order

        allowed = Order.STATUS_TRANSITIONS.get(order.status, ())

        if new_status not in allowed:
            raise ValueError(
                f"No se puede cambiar de '{order.status}' a '{new_status}'. "
                f"Transiciones permitidas: {', '.join(allowed) or 'ninguna'}."
            )

        prev_data = order.to_dict()

        # ── Reglas de negocio para el estado 'enviado' ──
        # Solo las órdenes con flete pueden pasar por 'enviado'.
        customer = order.customer
        has_freight = customer and customer.requires_freight

        if new_status == "enviado" and not has_freight:
            raise ValueError(
                "El estado 'Enviado' solo aplica para órdenes con envío (flete). "
                "Esta orden no tiene envío; use 'Entregado' directamente."
            )

        # Si la orden tiene flete y se intenta pasar de terminado a entregado
        # sin pasar por enviado, bloquear.
        if (
            new_status == "entregado"
            and order.status == "terminado"
            and has_freight
        ):
            raise ValueError(
                "Esta orden tiene envío. Primero debe marcarse como 'Enviado' "
                "antes de marcarla como 'Entregado'."
            )

        order.status = new_status

        # Al entregar, verificar que producción haya terminado todos los ítems
        if new_status == "entregado" and order.production_orders:
            pendientes = [
                po for po in order.production_orders if po.status != "terminado"
            ]
            if pendientes:
                productos = ", ".join(
                    po.product.name if po.product else f"#{po.id}" for po in pendientes
                )
                raise ValueError(
                    f"No se puede entregar: {len(pendientes)} orden(es) de producción "
                    f"aún no están terminadas ({productos})."
                )

        db.session.add(
            AuditLog(
                table_name="orders",
                action="UPDATE",
                user_id=user_id,
                timestamp=datetime.now(),
                previous_data=prev_data,
                new_data=order.to_dict(),
            )
        )

        db.session.commit()
        return order

    # ------------------------------------------------------------------ #
    #  Integración POS / Ecommerce                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_from_pos(
        *,
        customer_id: int,
        cart_items: list[dict],
        payment_method_id: Optional[int],
        employee_id: int,
        total: Decimal,
        sale_id: Optional[int] = None,
        estimated_delivery_date: Optional[date] = None,
    ) -> Order:
        """
        Crea una orden de cliente automáticamente desde el checkout del POS.

        Args:
            customer_id: ID del cliente.
            cart_items: Items del carrito [{product_id, name, price, quantity}].
            payment_method_id: ID del método de pago.
            employee_id: ID del empleado que procesa la venta.
            total: Total de la venta.
            estimated_delivery_date: Fecha estimada de entrega.

        Returns:
            Order: Orden creada.
        """
        if not estimated_delivery_date:
            from datetime import timedelta
            from app.models.customer import Customer
            from app.sales.freight_config import calculate_freight, LOCAL_DELIVERY_DAYS

            customer = Customer.query.get(customer_id)
            freight = calculate_freight(customer, total)
            days = freight.get("delivery_days") or LOCAL_DELIVERY_DAYS
            estimated_delivery_date = date.today() + timedelta(days=days)

        order = Order(
            customer_id=customer_id,
            order_date=datetime.now(),
            estimated_delivery_date=estimated_delivery_date,
            status="pendiente",
            total=total,
            payment_method_id=payment_method_id,
            notes="Generada automáticamente desde POS.",
            source="pos",
            created_by_id=employee_id,
            sale_id=sale_id,
        )
        db.session.add(order)
        db.session.flush()

        for item_data in cart_items:
            # El carrito del POS usa 'id' como product_id y 'subtotal'/
            # 'quantity' para derivar el precio unitario.
            product_id = item_data.get("product_id") or item_data.get("id")
            quantity = int(item_data.get("quantity", 1))
            # Precio unitario: puede venir como 'price' o derivado de subtotal/quantity
            unit_price = item_data.get("price")
            if unit_price is None:
                subtotal = item_data.get("subtotal", 0)
                unit_price = (
                    Decimal(str(subtotal)) / quantity if quantity else Decimal("0")
                )
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=int(product_id),
                    quantity=quantity,
                    price=Decimal(str(unit_price)),
                )
            )

        db.session.add(
            AuditLog(
                table_name="orders",
                action="INSERT",
                user_id=employee_id,
                timestamp=datetime.now(),
                previous_data=None,
                new_data=order.to_dict(),
            )
        )

        # Commit — la Sale ya fue committed por SaleService, aquí guardamos la Order
        db.session.commit()
        return order

    @staticmethod
    def create_from_ecommerce(
        *,
        customer_id: int,
        cart_items: list[dict],
        payment_method_id: Optional[int],
        total: Decimal,
        notes: str = "",
        estimated_delivery_date: Optional[date] = None,
    ) -> Order:
        """
        Crea una orden de cliente automáticamente desde checkout de ecommerce.

        Returns:
            Order: Orden creada.
        """
        if not estimated_delivery_date:
            from datetime import timedelta

            estimated_delivery_date = date.today() + timedelta(days=14)

        order = Order(
            customer_id=customer_id,
            order_date=datetime.now(),
            estimated_delivery_date=estimated_delivery_date,
            status="pendiente",
            total=total,
            payment_method_id=payment_method_id,
            notes=notes or "Generada automáticamente desde e-commerce.",
            source="ecommerce",
            created_by_id=None,
        )
        db.session.add(order)
        db.session.flush()

        for item_data in cart_items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    price=Decimal(str(item_data["price"])),
                )
            )

        db.session.add(
            AuditLog(
                table_name="orders",
                action="INSERT",
                user_id=None,
                timestamp=datetime.now(),
                previous_data=None,
                new_data=order.to_dict(),
            )
        )

        db.session.commit()
        return order
