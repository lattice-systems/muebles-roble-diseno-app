from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.costs.services import CostService
from app.models import Order, OrderItem, Product, ProductionOrder, ProductionOrderMaterial, Sale, SaleItem
from .mongo_service import ensure_report_indexes, get_report_collections


class ReportService:
    TAX_RATE = Decimal("0.16")

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
    def _build_recent_sale_row(source: str, record_id: int, record_date, total, payment_method_name: str | None):
        total_decimal = ReportService._to_decimal(total)
        subtotal = total_decimal / (Decimal("1.00") + ReportService.TAX_RATE)
        iva = total_decimal - subtotal

        return {
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
        start_dt, end_dt = ReportService._start_end_for_day(target_date)

        sales = (
            Sale.query.filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .all()
        )
        orders = (
            Order.query.filter(Order.order_date >= start_dt, Order.order_date <= end_dt)
            .all()
        )

        pos_total = sum(ReportService._to_decimal(s.total) for s in sales)
        ecommerce_total = sum(
            ReportService._to_decimal(o.total)
            for o in orders
            if str(o.status).lower() not in {"cancelada", "cancelled", "rechazada", "rejected"}
        )
        grand_total = pos_total + ecommerce_total

        payment_methods = defaultdict(lambda: {"amount": Decimal("0"), "count": 0})

        for sale in sales:
            method_name = (
                sale.payment_method.name
                if sale.payment_method is not None
                else "Sin método"
            )
            payment_methods[method_name]["amount"] += ReportService._to_decimal(sale.total)
            payment_methods[method_name]["count"] += 1

        for order in orders:
            if str(order.status).lower() in {"cancelada", "cancelled", "rechazada", "rejected"}:
                continue

            method_name = (
                order.payment_method.name
                if order.payment_method is not None
                else "Sin método"
            )
            payment_methods[method_name]["amount"] += ReportService._to_decimal(order.total)
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

        doc = {
            "report_date": target_date.isoformat(),
            "totals": {
                "pos_sales": ReportService._money(pos_total),
                "ecommerce_sales": ReportService._money(ecommerce_total),
                "grand_total": ReportService._money(grand_total),
                "transactions_count": len(sales) + len(orders),
            },
            "payment_methods": payment_methods_data,
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
        start_dt, end_dt = ReportService._start_end_for_day(target_date)

        sale_items = (
            SaleItem.query.join(Sale)
            .filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .all()
        )
        order_items = (
            OrderItem.query.join(Order)
            .filter(Order.order_date >= start_dt, Order.order_date <= end_dt)
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
            if str(item.order.status).lower() in {"cancelada", "cancelled", "rechazada", "rejected"}:
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

        products = []
        for row in product_rows.values():
            products.append(
                {
                    "product_id": row["product_id"],
                    "sku": row["sku"],
                    "product_name": row["product_name"],
                    "quantity_sold": row["quantity_sold"],
                    "revenue": ReportService._money(row["revenue"]),
                    "estimated_unit_cost": ReportService._money(row["estimated_unit_cost"]),
                    "estimated_total_cost": ReportService._money(row["estimated_total_cost"]),
                    "estimated_profit": ReportService._money(row["estimated_profit"]),
                }
            )

        products.sort(key=lambda x: x["estimated_profit"], reverse=True)
        estimated_profit_total = revenue_total - estimated_cost_total
        margin_pct = Decimal("0")
        if revenue_total > 0:
            margin_pct = (estimated_profit_total / revenue_total) * Decimal("100")

        doc = {
            "report_date": target_date.isoformat(),
            "revenue_total": ReportService._money(revenue_total),
            "estimated_cost_total": ReportService._money(estimated_cost_total),
            "estimated_profit_total": ReportService._money(estimated_profit_total),
            "margin_percentage": ReportService._money(margin_pct),
            "products": products,
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
            start_dt, end_dt = ReportService._start_end_for_day(current_day)

            pos_total = sum(
                ReportService._to_decimal(s.total)
                for s in Sale.query.filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt).all()
            )
            ecommerce_total = sum(
                ReportService._to_decimal(o.total)
                for o in Order.query.filter(Order.order_date >= start_dt, Order.order_date <= end_dt).all()
                if str(o.status).lower() not in {"cancelada", "cancelled", "rechazada", "rejected"}
            )

            total = pos_total + ecommerce_total
            if total > max_value:
                max_value = total

            items.append(
                {
                    "date": current_day.isoformat(),
                    "label": ReportService._weekday_name(current_day),
                    "amount": ReportService._money(total),
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
    def generate_top_products_snapshot(date_from: date | None = None, date_to: date | None = None) -> dict:
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
            .filter(Order.order_date >= start_dt, Order.order_date <= end_dt)
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
            if str(item.order.status).lower() in {"cancelada", "cancelled", "rechazada", "rejected"}:
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
    def generate_recent_sales_snapshot(target_date: date | None = None, limit: int = 10) -> dict:
        target_date = target_date or date.today()
        start_dt, end_dt = ReportService._start_end_for_day(target_date)

        rows = []

        sales = (
            Sale.query.filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .order_by(Sale.sale_date.desc(), Sale.id.desc())
            .all()
        )
        for sale in sales:
            rows.append(
                ReportService._build_recent_sale_row(
                    source="POS",
                    record_id=sale.id,
                    record_date=sale.sale_date,
                    total=sale.total,
                    payment_method_name=sale.payment_method.name if sale.payment_method else None,
                )
            )

        orders = (
            Order.query.filter(Order.order_date >= start_dt, Order.order_date <= end_dt)
            .order_by(Order.order_date.desc(), Order.id.desc())
            .all()
        )
        for order in orders:
            if str(order.status).lower() in {"cancelada", "cancelled", "rechazada", "rejected"}:
                continue

            rows.append(
                ReportService._build_recent_sale_row(
                    source="ECOM",
                    record_id=order.id,
                    record_date=order.order_date,
                    total=order.total,
                    payment_method_name=order.payment_method.name if order.payment_method else None,
                )
            )

        rows.sort(key=lambda x: x["sort_date"], reverse=True)
        rows = rows[:limit]

        for row in rows:
            row.pop("sort_date", None)

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

        completed_production_orders = ProductionOrder.query.filter(
            ProductionOrder.status.in_(["finalizada", "finished", "completed", "completada"])
        ).count()

        doc = {
            "report_date": target_date.isoformat(),
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
        recent_sales = ReportService.generate_recent_sales_snapshot(target_date, limit=10)
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
    def get_dashboard(target_date: date | None = None, force_refresh: bool = False) -> dict:
        target_date = target_date or date.today()
        ensure_report_indexes()
        collections = get_report_collections()

        if force_refresh:
            return ReportService.refresh_dashboard_snapshots(target_date)

        daily_sales = collections["daily_sales"].find_one({"report_date": target_date.isoformat()})
        daily_profit = collections["daily_profit"].find_one({"report_date": target_date.isoformat()})
        weekly_sales = collections["weekly_sales"].find_one({"report_date": target_date.isoformat()})
        recent_sales = collections["recent_sales"].find_one({"report_date": target_date.isoformat()})
        top_products = collections["top_products"].find_one(
            {
                "date_from": (target_date - timedelta(days=29)).isoformat(),
                "date_to": target_date.isoformat(),
            }
        )
        general = collections["general"].find_one({"report_date": target_date.isoformat()})

        if not all([daily_sales, daily_profit, weekly_sales, recent_sales, top_products, general]):
            return ReportService.refresh_dashboard_snapshots(target_date)

        return {
            "daily_sales": daily_sales,
            "daily_profit": daily_profit,
            "weekly_sales": weekly_sales,
            "top_products": top_products,
            "recent_sales": recent_sales,
            "general": general,
        }
    
    @staticmethod
    def get_raw_material_consumption_report(date_from: date | None = None, date_to: date | None = None) -> dict:
        date_to = date_to or date.today()
        date_from = date_from or (date_to - timedelta(days=29))

        rows = defaultdict(lambda: {
            "raw_material_id": None,
            "raw_material_name": "",
            "unit": "",
            "quantity_used": Decimal("0"),
            "estimated_waste": Decimal("0"),
            "products": [],
        })

        orders = ProductionOrder.query.filter(
            ProductionOrder.scheduled_date >= date_from,
            ProductionOrder.scheduled_date <= date_to,
            ProductionOrder.status.in_(["finalizada", "finished", "completed", "completada"])
        ).all()

        for order in orders:
            for material in order.material_consumptions:
                rm = material.raw_material
                key = rm.id

                rows[key]["raw_material_id"] = rm.id
                rows[key]["raw_material_name"] = rm.name
                rows[key]["unit"] = rm.unit.abbreviation if rm.unit else ""
                rows[key]["quantity_used"] += ReportService._to_decimal(material.quantity_used)
                rows[key]["estimated_waste"] += (
                    ReportService._to_decimal(material.quantity_used) *
                    (ReportService._to_decimal(material.waste_applied) / Decimal("100"))
                )

                rows[key]["products"].append({
                    "product_id": order.product.id,
                    "product_name": order.product.name,
                    "produced_quantity": order.quantity,
                })

        items = []
        for value in rows.values():
            items.append({
                "raw_material_id": value["raw_material_id"],
                "raw_material_name": value["raw_material_name"],
                "unit": value["unit"],
                "quantity_used": ReportService._money(value["quantity_used"]),
                "estimated_waste": ReportService._money(value["estimated_waste"]),
                "products": value["products"],
            })

        items.sort(key=lambda x: x["quantity_used"], reverse=True)

        return {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "items": items,
        }

    @staticmethod
    def get_general_report(date_from: date | None = None, date_to: date | None = None) -> dict:
        date_to = date_to or date.today()
        date_from = date_from or (date_to - timedelta(days=29))

        dashboard = ReportService.get_dashboard(target_date=date.today())
        consumption = ReportService.get_raw_material_consumption_report(date_from, date_to)

        completed_orders = ProductionOrder.query.filter(
            ProductionOrder.scheduled_date >= date_from,
            ProductionOrder.scheduled_date <= date_to,
            ProductionOrder.status.in_(["finalizada", "finished", "completed", "completada"])
        ).count()

        return {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "summary": {
                "sales_total": dashboard["daily_sales"]["totals"]["grand_total"],
                "estimated_profit_total": dashboard["daily_profit"]["estimated_profit_total"],
                "transactions_count": dashboard["daily_sales"]["totals"]["transactions_count"],
                "completed_production_orders": completed_orders,
                "raw_materials_consumed": len(consumption["items"]),
            },
            "sales": dashboard["daily_sales"],
            "profit": dashboard["daily_profit"],
            "top_products": dashboard["top_products"],
            "raw_material_consumption": consumption,
        }