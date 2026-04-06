from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.costs.services import CostService
from app.models import (
    Order,
    OrderItem,
    ProductionOrder,
    Sale,
    SaleItem,
)
from .mongo_service import ensure_report_indexes, get_report_collections


class ReportService:
    TAX_RATE = Decimal("0.16")
    PRODUCTION_COMPLETED_STATUSES = [
        "terminado",
        "finalizado",
        "finalizada",
        "finished",
        "completed",
        "completada",
    ]

    @staticmethod
    def _to_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _money(value) -> float:
        value = ReportService._to_decimal(value)
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _start_end_for_day(target_date: date):
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        return start_dt, end_dt

    @staticmethod
    def _normalize_date_range(
        date_from: date | None = None, date_to: date | None = None
    ) -> tuple[date, date]:
        date_to = date_to or date.today()
        date_from = date_from or date_to

        if date_from > date_to:
            date_from, date_to = date_to, date_from

        return date_from, date_to

    @staticmethod
    def _start_end_for_range(
        date_from: date | None = None, date_to: date | None = None
    ) -> tuple[datetime, datetime, date, date]:
        date_from, date_to = ReportService._normalize_date_range(date_from, date_to)
        start_dt = datetime.combine(date_from, time.min)
        end_dt = datetime.combine(date_to, time.max)
        return start_dt, end_dt, date_from, date_to

    @staticmethod
    def _invalid_order_statuses() -> set[str]:
        return {"cancelada", "cancelled", "rechazada", "rejected"}

    @staticmethod
    def _is_valid_order(order) -> bool:
        return str(order.status).lower() not in ReportService._invalid_order_statuses()

    @staticmethod
    def _is_completed_production_status(status: str | None) -> bool:
        return str(status or "").strip().lower() in {
            value.lower() for value in ReportService.PRODUCTION_COMPLETED_STATUSES
        }

    @staticmethod
    def _get_completed_production_orders_in_range(
        date_from: date | None = None, date_to: date | None = None
    ) -> list:
        date_from, date_to = ReportService._normalize_date_range(date_from, date_to)

        orders = ProductionOrder.query.filter(
            ProductionOrder.scheduled_date >= date_from,
            ProductionOrder.scheduled_date <= date_to,
        ).all()

        return [
            order
            for order in orders
            if ReportService._is_completed_production_status(order.status)
        ]

    @staticmethod
    def _get_sales_and_orders_in_range(
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list, list, date, date]:
        start_dt, end_dt, date_from, date_to = ReportService._start_end_for_range(
            date_from, date_to
        )

        sales = (
            Sale.query.filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .order_by(Sale.sale_date.desc(), Sale.id.desc())
            .all()
        )

        orders = (
            Order.query.filter(
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
                Order.source == "ecommerce",
            )
            .order_by(Order.order_date.desc(), Order.id.desc())
            .all()
        )

        valid_orders = [
            order for order in orders if ReportService._is_valid_order(order)
        ]

        return sales, valid_orders, date_from, date_to

    @staticmethod
    def _calculate_sales_summary(
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        sales, valid_orders, date_from, date_to = (
            ReportService._get_sales_and_orders_in_range(date_from, date_to)
        )

        pos_total = sum(ReportService._to_decimal(sale.total) for sale in sales)
        ecommerce_total = sum(
            ReportService._to_decimal(order.total) for order in valid_orders
        )
        grand_total = pos_total + ecommerce_total

        payment_methods = defaultdict(lambda: {"amount": Decimal("0"), "count": 0})

        for sale in sales:
            method_name = (
                sale.payment_method.name
                if sale.payment_method is not None
                else "Sin método"
            )
            payment_methods[method_name]["amount"] += ReportService._to_decimal(
                sale.total
            )
            payment_methods[method_name]["count"] += 1

        for order in valid_orders:
            method_name = (
                order.payment_method.name
                if order.payment_method is not None
                else "Sin método"
            )
            payment_methods[method_name]["amount"] += ReportService._to_decimal(
                order.total
            )
            payment_methods[method_name]["count"] += 1

        payment_methods_data = [
            {
                "method": method,
                "amount": ReportService._money(values["amount"]),
                "count": values["count"],
            }
            for method, values in payment_methods.items()
        ]
        payment_methods_data.sort(key=lambda x: x["amount"], reverse=True)

        return {
            "date_from": date_from,
            "date_to": date_to,
            "pos_total": pos_total,
            "ecommerce_total": ecommerce_total,
            "grand_total": grand_total,
            "transactions_count": len(sales) + len(valid_orders),
            "payment_methods": payment_methods_data,
        }

    @staticmethod
    def _calculate_profit_summary(
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        start_dt, end_dt, date_from, date_to = ReportService._start_end_for_range(
            date_from, date_to
        )

        sale_items = (
            SaleItem.query.join(Sale)
            .filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .all()
        )
        order_items = (
            OrderItem.query.join(Order)
            .filter(
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
                Order.source == "ecommerce",
            )
            .all()
        )

        product_rows: dict[int, dict] = {}
        revenue_total = Decimal("0")
        estimated_cost_total = Decimal("0")

        for item in sale_items:
            product = item.product
            qty = item.quantity or 0
            line_revenue = ReportService._to_decimal(item.price) * qty

            summary = CostService.calculate_product_cost_summary(product)
            estimated_unit_cost = (
                ReportService._to_decimal(summary["unit_cost"])
                if summary["unit_cost"] is not None
                else ReportService._to_decimal(summary["total_cost"])
            )
            line_cost = estimated_unit_cost * qty

            revenue_total += line_revenue
            estimated_cost_total += line_cost

            if product.id not in product_rows:
                product_rows[product.id] = {
                    "product_id": product.id,
                    "sku": product.sku,
                    "product_name": product.name,
                    "quantity_sold": 0,
                    "revenue": Decimal("0"),
                    "estimated_unit_cost": estimated_unit_cost,
                    "estimated_total_cost": Decimal("0"),
                    "estimated_profit": Decimal("0"),
                }

            row = product_rows[product.id]
            row["quantity_sold"] += qty
            row["revenue"] += line_revenue
            row["estimated_total_cost"] += line_cost
            row["estimated_profit"] = row["revenue"] - row["estimated_total_cost"]

        for item in order_items:
            if not ReportService._is_valid_order(item.order):
                continue

            product = item.product
            qty = item.quantity or 0
            line_revenue = ReportService._to_decimal(item.price) * qty

            summary = CostService.calculate_product_cost_summary(product)
            estimated_unit_cost = (
                ReportService._to_decimal(summary["unit_cost"])
                if summary["unit_cost"] is not None
                else ReportService._to_decimal(summary["total_cost"])
            )
            line_cost = estimated_unit_cost * qty

            revenue_total += line_revenue
            estimated_cost_total += line_cost

            if product.id not in product_rows:
                product_rows[product.id] = {
                    "product_id": product.id,
                    "sku": product.sku,
                    "product_name": product.name,
                    "quantity_sold": 0,
                    "revenue": Decimal("0"),
                    "estimated_unit_cost": estimated_unit_cost,
                    "estimated_total_cost": Decimal("0"),
                    "estimated_profit": Decimal("0"),
                }

            row = product_rows[product.id]
            row["quantity_sold"] += qty
            row["revenue"] += line_revenue
            row["estimated_total_cost"] += line_cost
            row["estimated_profit"] = row["revenue"] - row["estimated_total_cost"]

        products = [
            {
                "product_id": row["product_id"],
                "sku": row["sku"],
                "product_name": row["product_name"],
                "quantity_sold": row["quantity_sold"],
                "revenue": ReportService._money(row["revenue"]),
                "estimated_unit_cost": ReportService._money(
                    row["estimated_unit_cost"]
                ),
                "estimated_total_cost": ReportService._money(
                    row["estimated_total_cost"]
                ),
                "estimated_profit": ReportService._money(row["estimated_profit"]),
            }
            for row in product_rows.values()
        ]
        products.sort(key=lambda x: x["estimated_profit"], reverse=True)

        estimated_profit_total = revenue_total - estimated_cost_total
        margin_pct = Decimal("0")
        if revenue_total > 0:
            margin_pct = (estimated_profit_total / revenue_total) * Decimal("100")

        return {
            "date_from": date_from,
            "date_to": date_to,
            "revenue_total": revenue_total,
            "estimated_cost_total": estimated_cost_total,
            "estimated_profit_total": estimated_profit_total,
            "margin_percentage": margin_pct,
            "products": products,
        }

    @staticmethod
    def _previous_period(date_from: date, date_to: date) -> tuple[date, date]:
        delta_days = (date_to - date_from).days + 1
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=delta_days - 1)
        return prev_date_from, prev_date_to

    @staticmethod
    def _calculate_change(current_value, previous_value) -> float:
        current_value = ReportService._to_decimal(current_value)
        previous_value = ReportService._to_decimal(previous_value)

        if previous_value == 0:
            if current_value == 0:
                return 0.0
            return 100.0

        change = ((current_value - previous_value) / previous_value) * Decimal("100")
        return ReportService._money(change)

    @staticmethod
    def _weekday_name(target_date: date) -> str:
        names = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        return names[target_date.weekday()]

    @staticmethod
    def _build_recent_sale_row(
        source: str, record_id: int, record_date, total, payment_method_name: str | None
    ):
        total_decimal = ReportService._to_decimal(total)
        subtotal = total_decimal / (Decimal("1.00") + ReportService.TAX_RATE)
        iva = total_decimal - subtotal

        return {
            "row_id": f"{source}_{record_id}",
            "record_id": record_id,
            "source": source,
            "label": f"{'POS' if source == 'POS' else 'ECOM'} #{record_id}",
            "date": record_date.strftime("%d %b %Y") if record_date else "",
            "subtotal": ReportService._money(subtotal),
            "iva": ReportService._money(iva),
            "total": ReportService._money(total_decimal),
            "payment_method": payment_method_name or "N/D",
            "sort_date": record_date,
        }

    @staticmethod
    def generate_daily_sales_snapshot(target_date: date | None = None) -> dict:
        target_date = target_date or date.today()
        summary = ReportService._calculate_sales_summary(target_date, target_date)

        doc = {
            "report_date": target_date.isoformat(),
            "date_from": target_date.isoformat(),
            "date_to": target_date.isoformat(),
            "totals": {
                "pos_sales": ReportService._money(summary["pos_total"]),
                "ecommerce_sales": ReportService._money(summary["ecommerce_total"]),
                "grand_total": ReportService._money(summary["grand_total"]),
                "transactions_count": summary["transactions_count"],
            },
            "payment_methods": summary["payment_methods"],
            "generated_at": datetime.utcnow(),
        }

        collections = get_report_collections()
        collections["daily_sales"].replace_one(
            {"report_date": target_date.isoformat()},
            doc,
            upsert=True,
        )
        return doc

    @staticmethod
    def generate_daily_profit_snapshot(target_date: date | None = None) -> dict:
        target_date = target_date or date.today()
        summary = ReportService._calculate_profit_summary(target_date, target_date)

        doc = {
            "report_date": target_date.isoformat(),
            "date_from": target_date.isoformat(),
            "date_to": target_date.isoformat(),
            "revenue_total": ReportService._money(summary["revenue_total"]),
            "estimated_cost_total": ReportService._money(
                summary["estimated_cost_total"]
            ),
            "estimated_profit_total": ReportService._money(
                summary["estimated_profit_total"]
            ),
            "margin_percentage": ReportService._money(summary["margin_percentage"]),
            "products": summary["products"],
            "generated_at": datetime.utcnow(),
        }

        collections = get_report_collections()
        collections["daily_profit"].replace_one(
            {"report_date": target_date.isoformat()},
            doc,
            upsert=True,
        )
        return doc

    @staticmethod
    def generate_weekly_sales_snapshot(target_date: date | None = None) -> dict:
        target_date = target_date or date.today()
        start_date = target_date - timedelta(days=6)

        items = []
        max_value = Decimal("0")

        for i in range(7):
            current_day = start_date + timedelta(days=i)
            summary = ReportService._calculate_sales_summary(current_day, current_day)

            total = summary["grand_total"]
            if total > max_value:
                max_value = total

            items.append(
                {
                    "date": current_day.isoformat(),
                    "label": ReportService._weekday_name(current_day),
                    "amount": ReportService._money(total),
                    "pos_sales": ReportService._money(summary["pos_total"]),
                    "ecommerce_sales": ReportService._money(summary["ecommerce_total"]),
                    "transactions_count": summary["transactions_count"],
                }
            )

        doc = {
            "report_date": target_date.isoformat(),
            "date_from": start_date.isoformat(),
            "date_to": target_date.isoformat(),
            "items": items,
            "max_amount": ReportService._money(max_value),
            "generated_at": datetime.utcnow(),
        }

        collections = get_report_collections()
        collections["weekly_sales"].replace_one(
            {"report_date": target_date.isoformat()},
            doc,
            upsert=True,
        )
        return doc

    @staticmethod
    def generate_top_products_snapshot(
        date_from: date | None = None, date_to: date | None = None
    ) -> dict:
        date_to = date_to or date.today()
        date_from = date_from or (date_to - timedelta(days=29))

        start_dt = datetime.combine(date_from, time.min)
        end_dt = datetime.combine(date_to, time.max)

        rows: dict[int, dict] = {}

        sale_items = (
            SaleItem.query.join(Sale)
            .filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .all()
        )
        order_items = (
            OrderItem.query.join(Order)
            .filter(
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
                Order.source == "ecommerce",
            )
            .all()
        )

        for item in sale_items:
            product = item.product
            qty = item.quantity or 0
            revenue = ReportService._to_decimal(item.price) * qty

            if product.id not in rows:
                rows[product.id] = {
                    "product_id": product.id,
                    "sku": product.sku,
                    "product_name": product.name,
                    "quantity_sold": 0,
                    "revenue": Decimal("0"),
                    "pos_quantity": 0,
                    "ecommerce_quantity": 0,
                }

            rows[product.id]["quantity_sold"] += qty
            rows[product.id]["revenue"] += revenue
            rows[product.id]["pos_quantity"] += qty

        for item in order_items:
            if not ReportService._is_valid_order(item.order):
                continue

            product = item.product
            qty = item.quantity or 0
            revenue = ReportService._to_decimal(item.price) * qty

            if product.id not in rows:
                rows[product.id] = {
                    "product_id": product.id,
                    "sku": product.sku,
                    "product_name": product.name,
                    "quantity_sold": 0,
                    "revenue": Decimal("0"),
                    "pos_quantity": 0,
                    "ecommerce_quantity": 0,
                }

            rows[product.id]["quantity_sold"] += qty
            rows[product.id]["revenue"] += revenue
            rows[product.id]["ecommerce_quantity"] += qty

        items = []
        for row in rows.values():
            items.append(
                {
                    "product_id": row["product_id"],
                    "sku": row["sku"],
                    "product_name": row["product_name"],
                    "quantity_sold": row["quantity_sold"],
                    "revenue": ReportService._money(row["revenue"]),
                    "pos_quantity": row["pos_quantity"],
                    "ecommerce_quantity": row["ecommerce_quantity"],
                }
            )

        items.sort(key=lambda x: x["quantity_sold"], reverse=True)
        items = items[:5]

        doc = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "items": items,
            "generated_at": datetime.utcnow(),
        }

        collections = get_report_collections()
        collections["top_products"].replace_one(
            {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
            doc,
            upsert=True,
        )
        return doc

    @staticmethod
    def generate_recent_sales_snapshot(
        target_date: date | None = None, limit: int = 10
    ) -> dict:
        target_date = target_date or date.today()

        rows = ReportService.get_recent_sales_rows(target_date=target_date)

        if limit:
            rows = rows[:limit]

        doc = {
            "report_date": target_date.isoformat(),
            "items": rows,
            "generated_at": datetime.utcnow(),
        }

        collections = get_report_collections()
        collections["recent_sales"].replace_one(
            {"report_date": target_date.isoformat()},
            doc,
            upsert=True,
        )
        return doc

    @staticmethod
    def generate_general_snapshot(target_date: date | None = None) -> dict:
        target_date = target_date or date.today()

        daily_sales = ReportService.generate_daily_sales_snapshot(target_date)
        daily_profit = ReportService.generate_daily_profit_snapshot(target_date)
        completed_production_orders = len(
            ReportService._get_completed_production_orders_in_range(
                target_date, target_date
            )
        )

        doc = {
            "report_date": target_date.isoformat(),
            "date_from": target_date.isoformat(),
            "date_to": target_date.isoformat(),
            "summary": {
                "sales_total": daily_sales["totals"]["grand_total"],
                "estimated_profit_total": daily_profit["estimated_profit_total"],
                "completed_production_orders": completed_production_orders,
                "transactions_count": daily_sales["totals"]["transactions_count"],
            },
            "generated_at": datetime.utcnow(),
        }

        collections = get_report_collections()
        collections["general"].replace_one(
            {"report_date": target_date.isoformat()},
            doc,
            upsert=True,
        )
        return doc

    @staticmethod
    def refresh_dashboard_snapshots(target_date: date | None = None) -> dict:
        target_date = target_date or date.today()
        ensure_report_indexes()

        daily_sales = ReportService.generate_daily_sales_snapshot(target_date)
        daily_profit = ReportService.generate_daily_profit_snapshot(target_date)
        weekly_sales = ReportService.generate_weekly_sales_snapshot(target_date)
        top_products = ReportService.generate_top_products_snapshot(
            date_from=target_date - timedelta(days=29),
            date_to=target_date,
        )
        recent_sales = ReportService.generate_recent_sales_snapshot(
            target_date, limit=10
        )
        general = ReportService.generate_general_snapshot(target_date)

        return {
            "daily_sales": daily_sales,
            "daily_profit": daily_profit,
            "weekly_sales": weekly_sales,
            "top_products": top_products,
            "recent_sales": recent_sales,
            "general": general,
        }

    @staticmethod
    def get_dashboard(
        target_date: date | None = None, force_refresh: bool = False
    ) -> dict:
        target_date = target_date or date.today()
        ensure_report_indexes()
        collections = get_report_collections()

        if force_refresh:
            return ReportService.refresh_dashboard_snapshots(target_date)

        daily_sales = collections["daily_sales"].find_one(
            {"report_date": target_date.isoformat()}
        )
        daily_profit = collections["daily_profit"].find_one(
            {"report_date": target_date.isoformat()}
        )
        weekly_sales = collections["weekly_sales"].find_one(
            {"report_date": target_date.isoformat()}
        )
        recent_sales = collections["recent_sales"].find_one(
            {"report_date": target_date.isoformat()}
        )
        top_products = collections["top_products"].find_one(
            {
                "date_from": (target_date - timedelta(days=29)).isoformat(),
                "date_to": target_date.isoformat(),
            }
        )
        general = collections["general"].find_one(
            {"report_date": target_date.isoformat()}
        )

        snapshots = {
            "daily_sales": daily_sales,
            "daily_profit": daily_profit,
            "weekly_sales": weekly_sales,
            "recent_sales": recent_sales,
            "top_products": top_products,
            "general": general,
        }

        if not all(snapshots.values()):
            return ReportService.refresh_dashboard_snapshots(target_date)

        weekly_items = weekly_sales.get("items", []) if weekly_sales else []
        weekly_has_data_shape = len(weekly_items) == 7 and "max_amount" in weekly_sales

        if not weekly_has_data_shape:
            return ReportService.refresh_dashboard_snapshots(target_date)

        if recent_sales is not None and "items" not in recent_sales:
            return ReportService.refresh_dashboard_snapshots(target_date)

        if top_products is not None and "items" not in top_products:
            return ReportService.refresh_dashboard_snapshots(target_date)

        expected_total = daily_sales.get("totals", {}).get("grand_total", 0)
        weekly_last_day_amount = weekly_items[-1].get("amount", 0) if weekly_items else 0

        if expected_total and weekly_last_day_amount == 0:
            return ReportService.refresh_dashboard_snapshots(target_date)

        return snapshots

    @staticmethod
    def get_raw_material_consumption_report(
        date_from: date | None = None, date_to: date | None = None
    ) -> dict:
        date_from, date_to = ReportService._normalize_date_range(date_from, date_to)

        rows = defaultdict(
            lambda: {
                "raw_material_id": None,
                "raw_material_name": "",
                "unit": "",
                "quantity_used": Decimal("0"),
                "estimated_waste": Decimal("0"),
                "products": [],
            }
        )

        orders = ReportService._get_completed_production_orders_in_range(
            date_from, date_to
        )

        for order in orders:
            for material in order.material_consumptions:
                rm = material.raw_material
                key = rm.id

                rows[key]["raw_material_id"] = rm.id
                rows[key]["raw_material_name"] = rm.name
                rows[key]["unit"] = rm.unit.abbreviation if rm.unit else ""
                rows[key]["quantity_used"] += ReportService._to_decimal(
                    material.quantity_used
                )
                rows[key]["estimated_waste"] += ReportService._to_decimal(
                    material.quantity_used
                ) * (
                    ReportService._to_decimal(material.waste_applied)
                    / Decimal("100")
                )

                rows[key]["products"].append(
                    {
                        "product_id": order.product.id,
                        "product_name": order.product.name,
                        "produced_quantity": order.quantity,
                    }
                )

        items = []
        for value in rows.values():
            items.append(
                {
                    "raw_material_id": value["raw_material_id"],
                    "raw_material_name": value["raw_material_name"],
                    "unit": value["unit"],
                    "quantity_used": ReportService._money(value["quantity_used"]),
                    "estimated_waste": ReportService._money(value["estimated_waste"]),
                    "products": value["products"],
                }
            )

        items.sort(key=lambda x: x["quantity_used"], reverse=True)

        return {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "items": items,
        }

    @staticmethod
    def get_general_report(
        date_from: date | None = None, date_to: date | None = None
    ) -> dict:
        _, _, date_from, date_to = ReportService._start_end_for_range(
            date_from, date_to
        )

        sales_summary = ReportService._calculate_sales_summary(date_from, date_to)
        profit_summary = ReportService._calculate_profit_summary(date_from, date_to)
        consumption = ReportService.get_raw_material_consumption_report(
            date_from, date_to
        )
        top_products = ReportService.generate_top_products_snapshot(date_from, date_to)
        completed_orders = len(
            ReportService._get_completed_production_orders_in_range(date_from, date_to)
        )

        sales_doc = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "totals": {
                "pos_sales": ReportService._money(sales_summary["pos_total"]),
                "ecommerce_sales": ReportService._money(
                    sales_summary["ecommerce_total"]
                ),
                "grand_total": ReportService._money(sales_summary["grand_total"]),
                "transactions_count": sales_summary["transactions_count"],
            },
            "payment_methods": sales_summary["payment_methods"],
        }

        profit_doc = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "revenue_total": ReportService._money(profit_summary["revenue_total"]),
            "estimated_cost_total": ReportService._money(
                profit_summary["estimated_cost_total"]
            ),
            "estimated_profit_total": ReportService._money(
                profit_summary["estimated_profit_total"]
            ),
            "margin_percentage": ReportService._money(
                profit_summary["margin_percentage"]
            ),
            "products": profit_summary["products"],
        }

        return {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "summary": {
                "sales_total": sales_doc["totals"]["grand_total"],
                "estimated_profit_total": profit_doc["estimated_profit_total"],
                "transactions_count": sales_doc["totals"]["transactions_count"],
                "completed_production_orders": completed_orders,
                "raw_materials_consumed": len(consumption["items"]),
            },
            "sales": sales_doc,
            "profit": profit_doc,
            "top_products": top_products,
            "raw_material_consumption": consumption,
        }

    @staticmethod
    def get_recent_sales_rows(
        target_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search_term: str = "",
        source_filter: str = "all",
    ) -> list[dict]:
        if target_date is not None and date_from is None and date_to is None:
            date_from = target_date
            date_to = target_date

        sales, valid_orders, _, _ = ReportService._get_sales_and_orders_in_range(
            date_from, date_to
        )

        rows = []

        for sale in sales:
            rows.append(
                ReportService._build_recent_sale_row(
                    source="POS",
                    record_id=sale.id,
                    record_date=sale.sale_date,
                    total=sale.total,
                    payment_method_name=(
                        sale.payment_method.name if sale.payment_method else None
                    ),
                )
            )

        for order in valid_orders:
            rows.append(
                ReportService._build_recent_sale_row(
                    source="ECOM",
                    record_id=order.id,
                    record_date=order.order_date,
                    total=order.total,
                    payment_method_name=(
                        order.payment_method.name if order.payment_method else None
                    ),
                )
            )

        if source_filter == "pos":
            rows = [row for row in rows if row["source"] == "POS"]
        elif source_filter == "ecommerce":
            rows = [row for row in rows if row["source"] == "ECOM"]

        if search_term:
            term = search_term.strip().lower()
            rows = [
                row
                for row in rows
                if term in row["label"].lower()
                or term in row["date"].lower()
                or term in row["payment_method"].lower()
                or term in row["source"].lower()
            ]

        rows.sort(key=lambda x: x["sort_date"], reverse=True)

        for row in rows:
            row.pop("sort_date", None)

        return rows

    @staticmethod
    def get_dashboard_comparison_metrics(target_date: date | None = None) -> dict:
        target_date = target_date or date.today()

        current_sales = ReportService._calculate_sales_summary(target_date, target_date)
        previous_day = target_date - timedelta(days=1)
        previous_sales = ReportService._calculate_sales_summary(
            previous_day, previous_day
        )

        current_profit = ReportService._calculate_profit_summary(
            target_date, target_date
        )
        previous_profit = ReportService._calculate_profit_summary(
            previous_day, previous_day
        )

        sales_change_pct = ReportService._calculate_change(
            current_sales["grand_total"],
            previous_sales["grand_total"],
        )
        profit_change_pct = ReportService._calculate_change(
            current_profit["estimated_profit_total"],
            previous_profit["estimated_profit_total"],
        )

        return {
            "sales_change_pct": sales_change_pct,
            "profit_change_pct": profit_change_pct,
            "sales_direction": "up" if sales_change_pct >= 0 else "down",
            "profit_direction": "up" if profit_change_pct >= 0 else "down",
        }