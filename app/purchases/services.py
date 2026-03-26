"""
Servicios de lógica de negocio para compras (Purchase Orders).
"""

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.raw_material import RawMaterial
from app.models.raw_material_movement import RawMaterialMovement
from app.models.supplier import Supplier


class PurchaseOrderService:
    """Servicio para operaciones de negocio relacionadas con órdenes de compra."""

    @staticmethod
    def _log_audit(action: str, previous: dict | None, new: dict | None) -> None:
        """Registra un cambio en la tabla audit_log."""
        entry = AuditLog(
            table_name="purchase_orders",
            action=action,
            previous_data=previous,
            new_data=new,
        )
        db.session.add(entry)

    @staticmethod
    def get_supplier_choices() -> list[tuple[int, str]]:
        """Obtiene las opciones de proveedores activos para selectores."""
        suppliers = (
            Supplier.query.filter(Supplier.status.is_(True))
            .order_by(Supplier.name.asc())
            .all()
        )
        return [(s.id, s.name) for s in suppliers]

    @staticmethod
    def get_raw_material_choices() -> list[tuple[int, str]]:
        """Obtiene las opciones de materia prima para selectores, incluyendo su unidad."""
        materials = (
            RawMaterial.query.join(RawMaterial.unit)
            .order_by(RawMaterial.name.asc())
            .all()
        )
        return [(m.id, f"{m.name} ({m.unit.abbreviation})") for m in materials]

    @staticmethod
    def get_all(
        search_term: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """Obtiene órdenes de compra con búsqueda por proveedor/ID, filtro de estado y paginación."""
        query = PurchaseOrder.query.options(joinedload(PurchaseOrder.supplier))

        if status_filter and status_filter != "todos":
            query = query.filter(PurchaseOrder.status == status_filter.lower())

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            # Buscar por ID si es numérico, o por nombre del proveedor
            filters = [Supplier.name.ilike(term)]

            if search_term.strip().isdigit():
                # Comparación exacta o parcial para ID
                # (en MySql LIKE en int puede funcionar, o hacemos un match exacto)
                # Para mayor base de datos agnostic hacemos filter_by(id) si es exacto
                # Pero con SQLAlchemy cast a String funciona:
                from sqlalchemy import cast, String

                filters.append(cast(PurchaseOrder.id, String).ilike(term))

            query = query.join(PurchaseOrder.supplier).filter(or_(*filters))

        query = query.order_by(PurchaseOrder.id.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_by_id(id_order: int) -> PurchaseOrder:
        """Obtiene una orden de compra por su ID, pre-cargando proveedor e ítems."""
        order = (
            PurchaseOrder.query.options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items).joinedload(
                    PurchaseOrderItem.raw_material
                ),
            )
            .filter_by(id=id_order)
            .first()
        )

        if not order:
            raise NotFoundError(
                f"No se encontró una orden de compra con el folio {id_order}"
            )
        return order

    @staticmethod
    def get_by_ids(order_ids: list[int]) -> list[PurchaseOrder]:
        """Obtiene múltiples órdenes por sus IDs."""
        if not order_ids:
            return []
        return (
            PurchaseOrder.query.options(joinedload(PurchaseOrder.supplier))
            .filter(PurchaseOrder.id.in_(order_ids))
            .order_by(PurchaseOrder.id.desc())
            .all()
        )

    @staticmethod
    def create(data: dict, items_data: list[dict]) -> PurchaseOrder:
        """Crea una nueva orden de compra y sus ítems, calculando el total."""
        supplier_id = data.get("supplier_id")
        order_date = data.get("order_date")
        status = data.get("status", "pendiente")

        if not supplier_id:
            raise ValidationError("El proveedor es requerido")
        if not order_date:
            raise ValidationError("La fecha de orden es requerida")
        if not items_data:
            raise ValidationError("La orden debe tener al menos un ítem")

        supplier = db.session.get(Supplier, supplier_id)
        if not supplier or not supplier.status:
            raise ValidationError("El proveedor seleccionado no existe o está inactivo")

        order = PurchaseOrder(
            supplier_id=supplier_id,
            order_date=order_date,
            status=status,
            total=0,
        )
        db.session.add(order)
        db.session.flush()  # Obtiene el ID para los ítems

        total = 0
        for item in items_data:
            rm_id = item.get("raw_material_id")
            qty = float(item.get("quantity", 0))
            price = float(item.get("unit_price", 0))

            if not rm_id or qty <= 0 or price <= 0:
                raise ValidationError(
                    "Los detalles de la orden contienen datos inválidos"
                )

            order_item = PurchaseOrderItem(
                purchase_order_id=order.id,
                raw_material_id=rm_id,
                quantity=qty,
                unit_price=price,
            )
            db.session.add(order_item)
            total += qty * price

        order.total = total
        db.session.commit()

        PurchaseOrderService._log_audit("CREATE", None, order.to_dict())
        return order

    @staticmethod
    def update(id_order: int, data: dict, items_data: list[dict]) -> PurchaseOrder:
        """Actualiza una orden existente, siempre y cuando su estado sea pendiente."""
        order = PurchaseOrderService.get_by_id(id_order)

        if order.status != "pendiente":
            raise ConflictError("Solo se pueden editar órdenes en estado 'pendiente'")

        previous = order.to_dict()

        supplier_id = data.get("supplier_id")
        order_date = data.get("order_date")

        if not items_data:
            raise ValidationError("La orden debe tener al menos un ítem")

        if supplier_id and supplier_id != order.supplier_id:
            supplier = db.session.get(Supplier, supplier_id)
            if not supplier or not supplier.status:
                raise ValidationError(
                    "El proveedor seleccionado no existe o está inactivo"
                )
            order.supplier_id = supplier_id

        if order_date:
            order.order_date = order_date

        # Borrar ítems existentes y crearlos de nuevo
        PurchaseOrderItem.query.filter_by(purchase_order_id=order.id).delete()

        total = 0
        for item in items_data:
            rm_id = item.get("raw_material_id")
            qty = float(item.get("quantity", 0))
            price = float(item.get("unit_price", 0))

            if not rm_id or qty <= 0 or price <= 0:
                raise ValidationError(
                    "Los detalles de la orden contienen datos inválidos"
                )

            order_item = PurchaseOrderItem(
                purchase_order_id=order.id,
                raw_material_id=rm_id,
                quantity=qty,
                unit_price=price,
            )
            db.session.add(order_item)
            total += qty * price

        order.total = total
        db.session.commit()

        PurchaseOrderService._log_audit("UPDATE", previous, order.to_dict())
        return order

    @staticmethod
    def change_status(id_order: int, new_status: str) -> PurchaseOrder:
        """Cambia el estado de la orden respetando el ciclo de vida. Aplica a inventario si es recibida."""
        order = PurchaseOrderService.get_by_id(id_order)
        previous = order.to_dict()
        current = order.status

        # Validaciones del flujo de estados
        valid_transitions = {
            "pendiente": ["confirmada", "cancelada"],
            "confirmada": ["recibida", "cancelada"],
            "recibida": [],  # Estado final
            "cancelada": [],  # Estado final
        }

        if new_status not in valid_transitions.get(current, []):
            raise ConflictError(
                f"No se puede cambiar el estado de '{current.capitalize()}' a '{new_status.capitalize()}'"
            )

        order.status = new_status

        # Si el estado es recibida, impactar el inventario
        if new_status == "recibida":
            for item in order.items:
                raw_material = item.raw_material
                # Convertir Decimal a float, sumar y actualizar
                current_stock = float(raw_material.stock)
                added_qty = float(item.quantity)
                raw_material.stock = current_stock + added_qty

                # Registrar el movimiento
                movement = RawMaterialMovement(
                    raw_material_id=raw_material.id,
                    movement_type="ENTRADA",
                    quantity=added_qty,
                    reference=f"Compra OC-{order.id}",
                )
                db.session.add(movement)

        db.session.commit()
        PurchaseOrderService._log_audit(
            f"STATUS_{new_status.upper()}", previous, order.to_dict()
        )
        return order

    @staticmethod
    def delete(id_order: int) -> bool:
        """Elimina físicamente una orden si todavía está pendiente."""
        order = PurchaseOrderService.get_by_id(id_order)

        if order.status != "pendiente":
            raise ConflictError("Solo se pueden eliminar órdenes en estado 'pendiente'")

        previous = order.to_dict()

        # Eliminar items (también se podría usar cascade en la relación)
        PurchaseOrderItem.query.filter_by(purchase_order_id=order.id).delete()
        db.session.delete(order)
        db.session.commit()

        PurchaseOrderService._log_audit("DELETE", previous, None)
        return True
