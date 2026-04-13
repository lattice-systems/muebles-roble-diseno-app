from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import or_

from app.extensions import db
from app.models import Bom, Product, ProductionOrder, PurchaseOrderItem
from app.exceptions import NotFoundError


class CostService:
    LOW_MARGIN_THRESHOLD = Decimal("15.00")

    @staticmethod
    def _to_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _round_qty(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_primary_bom(product: Product):
        if not product or not product.id:
            return None

        return (
            Bom.query.filter(Bom.product_id == product.id)
            .order_by(Bom.updated_at.desc(), Bom.id.desc())
            .first()
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
        return CostService._to_decimal(latest_item.unit_price)

    @staticmethod
    def _get_latest_finished_production(product_id: int):
        final_statuses = [
            "terminado",
            "finalizado",
            "finalizada",
            "finished",
            "completed",
            "completada",
        ]

        return (
            ProductionOrder.query.filter(
                ProductionOrder.product_id == product_id,
                ProductionOrder.status.in_(final_statuses),
            )
            .order_by(ProductionOrder.scheduled_date.desc(), ProductionOrder.id.desc())
            .first()
        )

    @staticmethod
    def _calculate_recipe_detail(product: Product) -> dict:
        bom = CostService._get_primary_bom(product)

        if not bom:
            return {
                "bom": None,
                "detail_items": [],
                "material_cost": Decimal("0.00"),
                "total_cost": Decimal("0.00"),
            }

        detail_items = []
        material_cost = Decimal("0")

        items = sorted(bom.items, key=lambda x: x.id)

        for item in items:
            raw_material = item.raw_material
            quantity_required = CostService._to_decimal(item.quantity_required)
            waste_percentage = CostService._to_decimal(
                getattr(raw_material, "waste_percentage", 0)
            )
            unit_price = CostService._get_latest_unit_price(raw_material.id)

            waste_factor = Decimal("1") + (waste_percentage / Decimal("100"))
            line_total = quantity_required * unit_price * waste_factor
            material_cost += line_total

            unit_name = ""
            unit_abbreviation = ""

            if raw_material.unit:
                unit_name = raw_material.unit.name or ""
                unit_abbreviation = getattr(raw_material.unit, "abbreviation", "") or ""

            detail_items.append(
                {
                    "material_id": raw_material.id,
                    "material_name": raw_material.name,
                    "quantity_required": CostService._round_qty(quantity_required),
                    "unit_name": unit_name,
                    "unit_abbreviation": unit_abbreviation,
                    "waste_percentage": CostService._round_qty(waste_percentage),
                    "unit_price": CostService._round_money(unit_price),
                    "line_total": CostService._round_money(line_total),
                }
            )

        material_cost = CostService._round_money(material_cost)
        overhead_percentage = Decimal("0.30")  # 30% adicional sobre el costo de materiales
        total_cost: Decimal = material_cost * (Decimal("1.00") + overhead_percentage)

        return {
            "bom": bom,
            "detail_items": detail_items,
            "material_cost": material_cost,
            "total_cost": total_cost,
        }

    @staticmethod
    def _build_margin_status(
        margin_value: Decimal, margin_percentage: Decimal | None
    ) -> dict:
        if margin_percentage is None:
            return {"key": "no-data", "label": "Sin datos"}

        if margin_value < Decimal("0"):
            return {"key": "negative", "label": "Margen negativo"}

        if margin_value == Decimal("0"):
            return {"key": "zero", "label": "Sin margen"}

        if margin_percentage <= CostService.LOW_MARGIN_THRESHOLD:
            return {"key": "low", "label": "Margen bajo"}

        return {"key": "healthy", "label": "Rentable"}

    @staticmethod
    def calculate_product_cost_summary(product: Product) -> dict:
        recipe_data = CostService._calculate_recipe_detail(product)
        material_cost = CostService._to_decimal(recipe_data["material_cost"])
        total_cost = CostService._to_decimal(recipe_data["total_cost"])
        sale_price = CostService._to_decimal(product.price)

        latest_production = CostService._get_latest_finished_production(product.id)

        unit_cost = CostService._round_money(total_cost)
        margin_value = CostService._round_money(sale_price - total_cost)

        if sale_price > 0:
            margin_percentage = CostService._round_money(
                (margin_value / sale_price) * Decimal("100")
            )
        else:
            margin_percentage = None

        status = CostService._build_margin_status(margin_value, margin_percentage)

        return {
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "recipe_version": (
                recipe_data["bom"].version if recipe_data["bom"] else "Sin receta"
            ),
            "material_cost": CostService._round_money(material_cost),
            "total_cost": CostService._round_money(total_cost),
            "sale_price": CostService._round_money(sale_price),
            "latest_production_id": latest_production.id if latest_production else None,
            "latest_production_date": (
                latest_production.scheduled_date.isoformat()
                if latest_production and latest_production.scheduled_date
                else None
            ),
            "latest_production_quantity": (
                latest_production.quantity if latest_production else None
            ),
            "unit_cost": unit_cost,
            "margin_value": margin_value,
            "margin_percentage": margin_percentage,
            "status": status,
        }

    @staticmethod
    def get_all(search_term: str | None = None, page: int = 1, per_page: int = 10):
        query = Product.query

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.sku.ilike(term),
                )
            )

        query = query.order_by(Product.id.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_cost_rows(
        search_term: str | None = None, page: int = 1, per_page: int = 10
    ) -> dict:
        pagination = CostService.get_all(
            search_term=search_term,
            page=page,
            per_page=per_page,
        )

        items = [
            CostService.calculate_product_cost_summary(product)
            for product in pagination.items
        ]

        return {
            "items": items,
            "pagination": pagination,
        }

    @staticmethod
    def get_product_cost_detail(product_id: int) -> dict:
        product = db.session.get(Product, product_id)
        if not product:
            raise NotFoundError(f"No se encontró un producto con ID {product_id}")

        recipe_data = CostService._calculate_recipe_detail(product)
        summary = CostService.calculate_product_cost_summary(product)
        latest_production = CostService._get_latest_finished_production(product.id)

        return {
            "product": product,
            "bom": recipe_data["bom"],
            "detail_items": recipe_data["detail_items"],
            "summary": summary,
            "latest_production": latest_production,
        }

    @staticmethod
    def get_cost_rows_by_ids(product_ids: list[int]) -> list[dict]:
        if not product_ids:
            return []

        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_map = {product.id: product for product in products}

        ordered_products = [
            product_map[product_id]
            for product_id in product_ids
            if product_id in product_map
        ]
        return [
            CostService.calculate_product_cost_summary(product)
            for product in ordered_products
        ]

    @staticmethod
    def _generate_snapshot_data() -> dict:
        """Genera los datos actuales de costos para la snapshot."""
        pagination = CostService.get_all(search_term=None, page=1, per_page=100000)

        products_summary = []
        total_material_cost = Decimal("0")
        total_cost = Decimal("0")
        total_sale_price = Decimal("0")
        total_margin_value = Decimal("0")

        for product in pagination.items:
            # Resumen general del producto
            summary = CostService.calculate_product_cost_summary(product)

            # Detalles de materiales del producto
            recipe_data = CostService._calculate_recipe_detail(product)

            product_entry = {
                "product_id": summary["product_id"],
                "product_name": summary["product_name"],
                "sku": summary["sku"],
                "recipe_version": summary["recipe_version"],
                "material_cost": float(
                    CostService._round_money(summary["material_cost"])
                ),
                "total_cost": float(CostService._round_money(summary["total_cost"])),
                "sale_price": float(CostService._round_money(summary["sale_price"])),
                "margin_value": float(
                    CostService._round_money(summary["margin_value"])
                ),
                "margin_percentage": (
                    float(summary["margin_percentage"])
                    if summary["margin_percentage"]
                    else None
                ),
                "status": summary["status"]["key"],
                "materials": [
                    {
                        "material_id": item["material_id"],
                        "material_name": item["material_name"],
                        "quantity_required": float(item["quantity_required"]),
                        "unit_name": item["unit_name"],
                        "unit_abbreviation": item["unit_abbreviation"],
                        "waste_percentage": float(item["waste_percentage"]),
                        "unit_price": float(item["unit_price"]),
                        "line_total": float(item["line_total"]),
                    }
                    for item in recipe_data["detail_items"]
                ],
            }

            products_summary.append(product_entry)

            total_material_cost += CostService._to_decimal(summary["material_cost"])
            total_cost += CostService._to_decimal(summary["total_cost"])
            total_sale_price += CostService._to_decimal(summary["sale_price"])
            total_margin_value += CostService._to_decimal(summary["margin_value"])

        return {
            "summary": {
                "total_products": len(products_summary),
                "total_material_cost": CostService._to_decimal(total_material_cost),
                "total_cost": CostService._to_decimal(total_cost),
                "total_sale_price": CostService._to_decimal(total_sale_price),
                "total_margin_value": CostService._to_decimal(total_margin_value),
            },
            "products": products_summary,
        }

    @staticmethod
    def _generate_snapshot_hash(snapshot_data: dict) -> str:
        """Genera un hash SHA256 del snapshot para detectar cambios."""
        # Convertir Decimal a float para JSON serialización
        data_for_hash = json.dumps(snapshot_data, default=str, sort_keys=True)
        return hashlib.sha256(data_for_hash.encode()).hexdigest()

    @staticmethod
    def _get_latest_snapshot():
        """Obtiene el último snapshot de costos de MongoDB."""
        try:
            from app.reports.mongo_service import get_report_collections

            collections = get_report_collections()
            latest = collections["cost_snapshots"].find_one(
                sort=[("snapshot_date", -1)]
            )
            return latest
        except Exception:
            # Si hay error con MongoDB, retornar None
            return None

    @staticmethod
    def generate_snapshot_if_changed() -> dict:
        """
        Genera y guarda un snapshot de costos en MongoDB solo si hay cambios.

        Returns:
            dict: {
                "has_changes": bool,
                "snapshot_date": datetime,
                "previous_snapshot_date": datetime | None,
                "hash": str,
                "previous_hash": str | None,
            }
        """
        try:
            from app.reports.mongo_service import (
                get_report_collections,
                ensure_report_indexes,
            )

            # Asegurar que los índices existan
            ensure_report_indexes()

            # Generar datos y hash actuales
            snapshot_data = CostService._generate_snapshot_data()
            current_hash = CostService._generate_snapshot_hash(snapshot_data)
            snapshot_date = datetime.utcnow()

            # Obtener última snapshot
            latest_snapshot = CostService._get_latest_snapshot()
            previous_hash = latest_snapshot.get("hash") if latest_snapshot else None
            previous_snapshot_date = (
                latest_snapshot.get("snapshot_date") if latest_snapshot else None
            )

            # Comparar hashes
            has_changes = current_hash != previous_hash

            result = {
                "has_changes": has_changes,
                "snapshot_date": snapshot_date,
                "previous_snapshot_date": previous_snapshot_date,
                "hash": current_hash,
                "previous_hash": previous_hash,
            }

            # Guardar snapshot solo si hay cambios
            if has_changes:
                collections = get_report_collections()
                doc = {
                    "snapshot_date": snapshot_date.date().isoformat(),
                    "timestamp": snapshot_date,
                    "hash": current_hash,
                    "summary": {
                        "total_products": snapshot_data["summary"]["total_products"],
                        "total_material_cost": float(
                            CostService._round_money(
                                snapshot_data["summary"]["total_material_cost"]
                            )
                        ),
                        "total_cost": float(
                            CostService._round_money(
                                snapshot_data["summary"]["total_cost"]
                            )
                        ),
                        "total_sale_price": float(
                            CostService._round_money(
                                snapshot_data["summary"]["total_sale_price"]
                            )
                        ),
                        "total_margin_value": float(
                            CostService._round_money(
                                snapshot_data["summary"]["total_margin_value"]
                            )
                        ),
                    },
                    "products": snapshot_data["products"],
                    "total_items": len(snapshot_data["products"]),
                }

                collections["cost_snapshots"].replace_one(
                    {"snapshot_date": snapshot_date.date().isoformat()},
                    doc,
                    upsert=True,
                )

            return result
        except Exception as e:
            # Si hay error, registrar pero no fallar
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error generando snapshot de costos: {str(e)}")

            return {
                "has_changes": False,
                "snapshot_date": datetime.utcnow(),
                "previous_snapshot_date": None,
                "hash": None,
                "previous_hash": None,
                "error": str(e),
            }
