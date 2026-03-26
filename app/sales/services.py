"""
Servicios de lógica de negocio para el módulo de ventas POS.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale


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
            raise NotFoundError(
                f"No se encontró una venta activa con ID {sale_id}"
            )
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
        query = Product.query.filter_by(status=True)

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
