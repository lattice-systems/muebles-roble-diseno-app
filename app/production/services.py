"""
Servicios de lógica de negocio para Producción y Recetas (BOM).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models import (
    AuditLog,
    Bom,
    BomItem,
    Order,
    Product,
    ProductInventory,
    ProductionOrder,
    ProductionOrderMaterial,
    PurchaseOrderItem,
    RawMaterial,
    RawMaterialMovement,
)


class ProductionService:
    """Servicio central para Recetas (BOM) y Producción."""

    @staticmethod
    def _to_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _log_audit(
        *,
        table_name: str,
        action: str,
        user_id: int | None,
        previous_data: dict | None,
        new_data: dict | None,
    ) -> None:
        db.session.add(
            AuditLog(
                table_name=table_name,
                action=action,
                user_id=user_id,
                timestamp=datetime.now(),
                previous_data=previous_data,
                new_data=new_data,
            )
        )

    @staticmethod
    def _get_latest_unit_price(raw_material_id: int) -> Decimal:
        latest_item = (
            PurchaseOrderItem.query.filter_by(raw_material_id=raw_material_id)
            .order_by(PurchaseOrderItem.id.desc())
            .first()
        )
        if not latest_item or latest_item.unit_price is None:
            return Decimal("0")
        return ProductionService._to_decimal(latest_item.unit_price)

    @staticmethod
    def _get_latest_bom(product_id: int) -> Bom | None:
        return (
            Bom.query.options(
                selectinload(Bom.items).selectinload(BomItem.raw_material)
            )
            .filter(Bom.product_id == product_id)
            .order_by(Bom.id.desc())
            .first()
        )

    @staticmethod
    def _normalize_bom_items(items_data: list[dict]) -> list[tuple[int, Decimal]]:
        if not items_data:
            raise ValidationError("La receta debe contener al menos un material")

        normalized: list[tuple[int, Decimal]] = []
        raw_material_ids: set[int] = set()

        for idx, item in enumerate(items_data, start=1):
            try:
                raw_material_id = int(item.get("raw_material_id", 0))
            except (TypeError, ValueError):
                raise ValidationError(f"Materia prima inválida en el renglón {idx}")

            quantity_required = ProductionService._to_decimal(
                item.get("quantity_required", 0)
            )

            if raw_material_id <= 0:
                raise ValidationError(
                    f"Debe seleccionar una materia prima válida en el renglón {idx}"
                )

            if quantity_required <= 0:
                raise ValidationError(
                    f"La cantidad requerida debe ser mayor a 0 en el renglón {idx}"
                )

            if raw_material_id in raw_material_ids:
                raise ValidationError(
                    "No se puede repetir la misma materia prima en la receta"
                )

            raw_material_ids.add(raw_material_id)
            normalized.append((raw_material_id, quantity_required))

        found_ids = {
            row.id
            for row in RawMaterial.query.filter(
                RawMaterial.id.in_(raw_material_ids)
            ).all()
        }
        missing = raw_material_ids - found_ids
        if missing:
            raise NotFoundError(
                "Una o más materias primas no existen o no están disponibles"
            )

        return normalized

    # ------------------------------------------------------------------ #
    #  Choices para formularios                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_product_choices(
        include_inactive_id: int | None = None,
    ) -> list[tuple[int, str]]:
        query = Product.query
        if include_inactive_id is not None:
            query = query.filter(
                or_(Product.status.is_(True), Product.id == include_inactive_id)
            )
        else:
            query = query.filter(Product.status.is_(True))

        products = query.order_by(Product.name.asc()).all()
        return [(p.id, f"{p.sku} - {p.name}") for p in products]

    @staticmethod
    def get_raw_material_choices(
        include_inactive_ids: list[int] | None = None,
    ) -> list[tuple[int, str]]:
        query = RawMaterial.query.options(joinedload(RawMaterial.unit))
        if include_inactive_ids:
            query = query.filter(
                or_(
                    RawMaterial.status == "active",
                    RawMaterial.id.in_(include_inactive_ids),
                )
            )
        else:
            query = query.filter(RawMaterial.status == "active")

        materials = query.order_by(RawMaterial.name.asc()).all()
        return [(m.id, f"{m.name} ({m.unit.abbreviation})") for m in materials]

    # ------------------------------------------------------------------ #
    #  BOM                                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_boms(search_term: str | None = None, page: int = 1, per_page: int = 10):
        query = Bom.query.options(
            joinedload(Bom.product),
            selectinload(Bom.items).joinedload(BomItem.raw_material),
        )

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.join(Bom.product).filter(
                or_(
                    Product.name.ilike(term),
                    Product.sku.ilike(term),
                    Bom.version.ilike(term),
                )
            )

        return query.order_by(Bom.id.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

    @staticmethod
    def get_bom_by_id(bom_id: int) -> Bom:
        bom = (
            Bom.query.options(
                joinedload(Bom.product),
                selectinload(Bom.items)
                .joinedload(BomItem.raw_material)
                .joinedload(RawMaterial.unit),
            )
            .filter(Bom.id == bom_id)
            .first()
        )

        if not bom:
            raise NotFoundError("Receta BOM no encontrada")
        return bom

    @staticmethod
    def create_bom(
        *,
        product_id: int,
        version: str,
        description: str,
        items_data: list[dict],
        user_id: int | None,
    ) -> Bom:
        product = db.session.get(Product, product_id)
        if not product:
            raise NotFoundError("Producto no encontrado")

        clean_version = (version or "").strip()
        if not clean_version:
            raise ValidationError("La versión de la receta es obligatoria")

        existing = Bom.query.filter_by(
            product_id=product_id, version=clean_version
        ).first()
        if existing:
            raise ConflictError("Ya existe una receta con esa versión para el producto")

        normalized_items = ProductionService._normalize_bom_items(items_data)

        try:
            bom = Bom(
                product_id=product_id,
                version=clean_version,
                description=(description or "").strip() or None,
                created_by=user_id,
                updated_by=user_id,
            )
            db.session.add(bom)
            db.session.flush()

            for raw_material_id, quantity_required in normalized_items:
                db.session.add(
                    BomItem(
                        bom_id=bom.id,
                        raw_material_id=raw_material_id,
                        quantity_required=quantity_required,
                    )
                )

            ProductionService._log_audit(
                table_name="bom",
                action="INSERT",
                user_id=user_id,
                previous_data=None,
                new_data=bom.to_dict(),
            )

            db.session.commit()
            return bom
        except (ValidationError, ConflictError, NotFoundError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"No fue posible crear la receta: {str(e)}")

    @staticmethod
    def update_bom(
        *,
        bom_id: int,
        version: str,
        description: str,
        items_data: list[dict],
        user_id: int | None,
    ) -> Bom:
        bom = ProductionService.get_bom_by_id(bom_id)

        clean_version = (version or "").strip()
        if not clean_version:
            raise ValidationError("La versión de la receta es obligatoria")

        duplicate = Bom.query.filter(
            Bom.product_id == bom.product_id,
            Bom.version == clean_version,
            Bom.id != bom.id,
        ).first()
        if duplicate:
            raise ConflictError(
                "Ya existe otra receta con esa versión para el producto"
            )

        normalized_items = ProductionService._normalize_bom_items(items_data)

        previous_data = bom.to_dict()

        try:
            bom.version = clean_version
            bom.description = (description or "").strip() or None
            bom.updated_by = user_id

            for item in list(bom.items):
                db.session.delete(item)
            db.session.flush()

            for raw_material_id, quantity_required in normalized_items:
                db.session.add(
                    BomItem(
                        bom_id=bom.id,
                        raw_material_id=raw_material_id,
                        quantity_required=quantity_required,
                    )
                )

            ProductionService._log_audit(
                table_name="bom",
                action="UPDATE",
                user_id=user_id,
                previous_data=previous_data,
                new_data=bom.to_dict(),
            )

            db.session.commit()
            return bom
        except (ValidationError, ConflictError, NotFoundError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"No fue posible actualizar la receta: {str(e)}")

    # ------------------------------------------------------------------ #
    #  Órdenes de producción                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_production_orders(
        *,
        search_term: str | None = None,
        status_filter: str = "all",
        page: int = 1,
        per_page: int = 10,
    ):
        query = ProductionOrder.query.options(
            joinedload(ProductionOrder.product),
            joinedload(ProductionOrder.customer_order),
        )

        if status_filter and status_filter != "all":
            query = query.filter(ProductionOrder.status == status_filter)

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.join(ProductionOrder.product).filter(
                or_(Product.name.ilike(term), Product.sku.ilike(term))
            )

        return query.order_by(
            ProductionOrder.scheduled_date.asc(),
            ProductionOrder.id.desc(),
        ).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_production_order_by_id(order_id: int) -> ProductionOrder:
        order = (
            ProductionOrder.query.options(
                joinedload(ProductionOrder.product),
                joinedload(ProductionOrder.customer_order).joinedload(Order.customer),
                selectinload(ProductionOrder.material_consumptions)
                .joinedload(ProductionOrderMaterial.raw_material)
                .joinedload(RawMaterial.unit),
            )
            .filter(ProductionOrder.id == order_id)
            .first()
        )

        if not order:
            raise NotFoundError("Orden de producción no encontrada")

        return order

    @staticmethod
    def get_allowed_status_transitions(order: ProductionOrder) -> tuple[str, ...]:
        """Retorna los estados destino permitidos para una orden de producción."""
        return ProductionOrder.STATUS_TRANSITIONS.get(order.status, ())

    @staticmethod
    def initialize_material_plan_for_order(
        production_order: ProductionOrder,
    ) -> list[ProductionOrderMaterial]:
        if production_order.material_consumptions:
            return list(production_order.material_consumptions)

        bom = ProductionService._get_latest_bom(production_order.product_id)
        if not bom:
            raise ValidationError(
                "El producto no tiene una receta BOM para generar consumo planificado"
            )

        if not bom.items:
            raise ValidationError("La receta BOM no tiene materiales asociados")

        materials: list[ProductionOrderMaterial] = []

        for item in sorted(bom.items, key=lambda x: x.id):
            planned_qty = ProductionService._to_decimal(
                item.quantity_required
            ) * Decimal(production_order.quantity)
            raw_material = item.raw_material

            material = ProductionOrderMaterial(
                production_order_id=production_order.id,
                raw_material_id=raw_material.id,
                quantity_planned=planned_qty,
                quantity_used=Decimal("0"),
                unit_cost=ProductionService._get_latest_unit_price(raw_material.id),
                waste_applied=ProductionService._to_decimal(
                    raw_material.waste_percentage
                ),
            )
            db.session.add(material)
            materials.append(material)

        return materials

    @staticmethod
    def initialize_material_plan(
        *,
        production_order_id: int,
        user_id: int | None,
    ) -> list[ProductionOrderMaterial]:
        order = ProductionService.get_production_order_by_id(production_order_id)

        previous_data = order.to_dict()

        try:
            materials = ProductionService.initialize_material_plan_for_order(order)
            order.updated_by = user_id

            ProductionService._log_audit(
                table_name="production_orders",
                action="UPDATE",
                user_id=user_id,
                previous_data=previous_data,
                new_data=order.to_dict(),
            )

            db.session.commit()
            return materials
        except Exception as e:
            db.session.rollback()
            raise ValidationError(
                f"No fue posible inicializar materiales planificados: {str(e)}"
            )

    @staticmethod
    def create_production_order(
        *,
        product_id: int,
        quantity: int,
        scheduled_date: date,
        user_id: int | None,
        customer_order_id: int | None = None,
    ) -> ProductionOrder:
        product = db.session.get(Product, product_id)
        if not product:
            raise NotFoundError("Producto no encontrado")

        if quantity <= 0:
            raise ValidationError("La cantidad a producir debe ser mayor a 0")

        try:
            order = ProductionOrder(
                product_id=product_id,
                quantity=quantity,
                status="pendiente",
                scheduled_date=scheduled_date,
                customer_order_id=customer_order_id,
                created_by=user_id,
                updated_by=user_id,
            )
            db.session.add(order)
            db.session.flush()

            ProductionService.initialize_material_plan_for_order(order)

            ProductionService._log_audit(
                table_name="production_orders",
                action="INSERT",
                user_id=user_id,
                previous_data=None,
                new_data=order.to_dict(),
            )

            db.session.commit()
            return order
        except (ValidationError, ConflictError, NotFoundError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationError(
                f"No fue posible crear la orden de producción: {str(e)}"
            )

    @staticmethod
    def update_material_usage(
        *,
        production_order_id: int,
        materials_data: list[dict],
        user_id: int | None,
    ) -> ProductionOrder:
        order = ProductionService.get_production_order_by_id(production_order_id)

        if order.status in ("terminado", "cancelado"):
            raise ConflictError(
                "No se puede registrar consumo en una orden terminada o cancelada"
            )

        if not order.material_consumptions:
            raise ValidationError(
                "La orden no tiene consumo planificado. Inicializa la receta primero"
            )

        if not materials_data:
            raise ValidationError("No se recibieron materiales para actualizar")

        by_raw_material = {
            row.raw_material_id: row for row in order.material_consumptions
        }

        previous_data = order.to_dict()
        updated_rows = 0

        try:
            for row in materials_data:
                raw_material_id = int(row.get("raw_material_id", 0))
                quantity_used = ProductionService._to_decimal(
                    row.get("quantity_used", 0)
                )
                material_row = by_raw_material.get(raw_material_id)
                if not material_row:
                    raise ValidationError(
                        "Uno de los materiales enviados no pertenece a esta orden"
                    )

                waste_applied = ProductionService._to_decimal(
                    row.get("waste_applied", material_row.waste_applied)
                )

                if quantity_used < 0:
                    raise ValidationError("La cantidad usada no puede ser negativa")

                if waste_applied < 0 or waste_applied > 100:
                    raise ValidationError("La merma aplicada debe estar entre 0 y 100")

                material_row.quantity_used = quantity_used
                material_row.waste_applied = waste_applied
                updated_rows += 1

            if updated_rows == 0:
                raise ValidationError("No se actualizaron materiales")

            order.updated_by = user_id

            ProductionService._log_audit(
                table_name="production_orders",
                action="UPDATE",
                user_id=user_id,
                previous_data=previous_data,
                new_data=order.to_dict(),
            )

            db.session.commit()
            return order
        except (ValidationError, ConflictError, NotFoundError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"No fue posible actualizar consumos: {str(e)}")

    @staticmethod
    def _consume_materials_and_update_inventory(
        order: ProductionOrder,
        *,
        user_id: int | None,
    ) -> None:
        if not order.material_consumptions:
            ProductionService.initialize_material_plan_for_order(order)

        consumptions: list[tuple[ProductionOrderMaterial, Decimal]] = []

        for material in order.material_consumptions:
            planned = ProductionService._to_decimal(material.quantity_planned)
            used = ProductionService._to_decimal(material.quantity_used)
            consume_qty = used if used > 0 else planned

            if consume_qty <= 0:
                continue

            stock = ProductionService._to_decimal(material.raw_material.stock)
            if stock < consume_qty:
                raise ConflictError(
                    f"Stock insuficiente de {material.raw_material.name}. "
                    f"Disponible: {stock}, requerido: {consume_qty}"
                )

            consumptions.append((material, consume_qty))

        for material, consume_qty in consumptions:
            raw_material = material.raw_material
            raw_material.stock = (
                ProductionService._to_decimal(raw_material.stock) - consume_qty
            )
            material.quantity_used = consume_qty

            db.session.add(
                RawMaterialMovement(
                    raw_material_id=raw_material.id,
                    movement_type="PRODUCCION",
                    quantity=consume_qty,
                    reason=f"Consumo por orden de producción OP-{order.id}",
                    reference=f"OP-{order.id}",
                    created_by=user_id,
                    updated_by=user_id,
                )
            )

        inventory = ProductInventory.query.filter_by(
            product_id=order.product_id
        ).first()
        if inventory:
            inventory.stock = int(inventory.stock or 0) + int(order.quantity)
            inventory.updated_by = user_id
        else:
            db.session.add(
                ProductInventory(
                    product_id=order.product_id,
                    stock=int(order.quantity),
                    created_by=user_id,
                    updated_by=user_id,
                )
            )

    @staticmethod
    def _sync_customer_order_status(
        order: ProductionOrder, user_id: int | None
    ) -> None:
        customer_order = order.customer_order
        if not customer_order:
            return

        if customer_order.status != "en_produccion":
            return

        if any(po.status != "terminado" for po in customer_order.production_orders):
            return

        previous_data = customer_order.to_dict()
        customer_order.status = "terminado"

        ProductionService._log_audit(
            table_name="orders",
            action="UPDATE",
            user_id=user_id,
            previous_data=previous_data,
            new_data=customer_order.to_dict(),
        )

    @staticmethod
    def change_production_order_status(
        *,
        production_order_id: int,
        new_status: str,
        user_id: int | None,
    ) -> ProductionOrder:
        order = ProductionService.get_production_order_by_id(production_order_id)

        target_status = (new_status or "").strip()
        if target_status not in ProductionOrder.VALID_STATUSES:
            raise ValidationError("Estado de producción inválido")

        if order.status == target_status:
            return order

        allowed = ProductionOrder.STATUS_TRANSITIONS.get(order.status, ())
        if target_status not in allowed:
            raise ConflictError(
                f"No se puede cambiar de '{order.status}' a '{target_status}'"
            )

        previous_data = order.to_dict()

        try:
            if target_status == "en_proceso":
                ProductionService.initialize_material_plan_for_order(order)

            if target_status == "terminado":
                ProductionService._consume_materials_and_update_inventory(
                    order,
                    user_id=user_id,
                )

            order.status = target_status
            order.updated_by = user_id

            if target_status == "terminado":
                ProductionService._sync_customer_order_status(order, user_id)

            ProductionService._log_audit(
                table_name="production_orders",
                action="UPDATE",
                user_id=user_id,
                previous_data=previous_data,
                new_data=order.to_dict(),
            )

            db.session.commit()
            return order
        except (ValidationError, ConflictError, NotFoundError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationError(
                f"No fue posible cambiar el estado de la orden: {str(e)}"
            )
