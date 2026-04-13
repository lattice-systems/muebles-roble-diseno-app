from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import (
    Order,
    OrderItem,
    ProductionOrder,
    ProductInventory,
    RawMaterial,
    Sale,
    SaleItem,
)
from app.costs.services import CostService


class DashboardService:
    @staticmethod
    def _to_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _get_day_bounds(target_date: date):
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        return start_dt, end_dt

    @staticmethod
    def get_daily_sales_kpi(target_date: date | None = None) -> dict:
        """Returns Pos + Ecommerce sales for a specific date."""
        target_date = target_date or date.today()
        start_dt, end_dt = DashboardService._get_day_bounds(target_date)

        pos_sales = Sale.query.filter(
            Sale.sale_date >= start_dt, Sale.sale_date <= end_dt
        ).all()
        ecommerce_orders = Order.query.filter(
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
            Order.source == "ecommerce",
        ).all()

        pos_total = sum(DashboardService._to_decimal(s.total) for s in pos_sales)
        ecommerce_total = sum(
            DashboardService._to_decimal(o.total)
            for o in ecommerce_orders
            if str(o.status).lower()
            not in {"cancelada", "cancelled", "rechazada", "rejected"}
        )

        return {
            "pos_total": float(pos_total),
            "ecommerce_total": float(ecommerce_total),
            "grand_total": float(pos_total + ecommerce_total),
            "transactions_count": len(pos_sales) + len(ecommerce_orders),
        }

    @staticmethod
    def get_production_kpi() -> dict:
        """Returns active production orders and products completed this month."""
        active_statuses = ["pendiente", "en_proceso", "pending", "in_progress"]
        completed_statuses = [
            "terminado",
            "finalizado",
            "finalizada",
            "finished",
            "completed",
            "completada",
        ]

        active_orders = ProductionOrder.query.filter(
            ProductionOrder.status.in_(active_statuses)
        ).count()

        today = date.today()
        first_day_of_month = today.replace(day=1)
        start_dt = datetime.combine(first_day_of_month, time.min)

        completed_quantity = (
            db.session.query(func.sum(ProductionOrder.quantity))
            .filter(
                ProductionOrder.status.in_(completed_statuses),
                ProductionOrder.updated_at >= start_dt,
            )
            .scalar()
            or 0
        )

        return {
            "active_orders_count": active_orders,
            "completed_products_this_month": int(completed_quantity),
        }

    @staticmethod
    def get_inventory_kpi() -> dict:
        """Returns total finished goods in stock and count of low stock raw materials."""
        total_products_stock = (
            db.session.query(func.sum(ProductInventory.stock)).scalar() or 0
        )

        low_stock_materials = (
            db.session.query(func.count(RawMaterial.id))
            .filter(
                RawMaterial.stock <= RawMaterial.minimum_stock,
                RawMaterial.status == "active",
            )
            .scalar()
            or 0
        )

        return {
            "total_products_stock": int(total_products_stock),
            "low_stock_materials_count": low_stock_materials,
        }

    @staticmethod
    def get_profit_kpi(target_date: date | None = None) -> dict:
        """Estimates profit for a specific date."""
        target_date = target_date or date.today()
        start_dt, end_dt = DashboardService._get_day_bounds(target_date)

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

        revenue_total = Decimal("0")
        estimated_cost_total = Decimal("0")

        # POS
        for item in sale_items:
            qty = DashboardService._to_decimal(item.quantity or 0)
            line_revenue = DashboardService._to_decimal(item.price) * qty

            summary = CostService.calculate_product_cost_summary(item.product)
            unit_cost = DashboardService._to_decimal(
                summary["unit_cost"] or summary["total_cost"] or 0
            )
            line_cost = unit_cost * qty

            revenue_total += line_revenue
            estimated_cost_total += line_cost

        # ECOMMERCE
        for item in order_items:
            if str(item.order.status).lower() in {
                "cancelada",
                "cancelled",
                "rechazada",
                "rejected",
            }:
                continue

            qty = DashboardService._to_decimal(item.quantity or 0)
            line_revenue = DashboardService._to_decimal(item.price) * qty

            summary = CostService.calculate_product_cost_summary(item.product)
            unit_cost = DashboardService._to_decimal(
                summary["unit_cost"] or summary["total_cost"] or 0
            )
            line_cost = unit_cost * qty

            revenue_total += line_revenue
            estimated_cost_total += line_cost

        profit = revenue_total - estimated_cost_total
        margin_pct = (
            (profit / revenue_total * 100) if revenue_total > 0 else Decimal("0")
        )

        return {
            "revenue": float(revenue_total),
            "cost": float(estimated_cost_total),
            "profit": float(profit),
            "margin_percentage": float(margin_pct),
        }

    @staticmethod
    def get_weekly_sales_chart(target_date: date | None = None) -> dict:
        """Data for ApexCharts area chart (last 7 days)."""
        target_date = target_date or date.today()
        start_date = target_date - timedelta(days=6)

        categories = []
        series_data = []

        weekday_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

        for i in range(7):
            current_day = start_date + timedelta(days=i)
            start_dt, end_dt = DashboardService._get_day_bounds(current_day)

            pos_total = sum(
                DashboardService._to_decimal(s.total)
                for s in Sale.query.filter(
                    Sale.sale_date >= start_dt, Sale.sale_date <= end_dt
                ).all()
            )
            ecommerce_total = sum(
                DashboardService._to_decimal(o.total)
                for o in Order.query.filter(
                    Order.order_date >= start_dt,
                    Order.order_date <= end_dt,
                    Order.source == "ecommerce",
                ).all()
                if str(o.status).lower()
                not in {"cancelada", "cancelled", "rechazada", "rejected"}
            )

            categories.append(
                f"{weekday_names[current_day.weekday()]} {current_day.day}"
            )
            series_data.append(float(pos_total + ecommerce_total))

        return {
            "categories": categories,
            "series": [{"name": "Ventas Totales", "data": series_data}],
        }

    @staticmethod
    def get_top_products_chart(target_date: date | None = None) -> dict:
        """Data for ApexCharts horizontal bar (last 30 days)."""
        target_date = target_date or date.today()
        start_date = target_date - timedelta(days=29)

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(target_date, time.max)

        product_sales = defaultdict(int)

        for item in (
            SaleItem.query.join(Sale)
            .filter(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)
            .all()
        ):
            product_sales[item.product.name] += item.quantity or 0

        for item in (
            OrderItem.query.join(Order)
            .filter(
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
                Order.source == "ecommerce",
            )
            .all()
        ):
            if str(item.order.status).lower() not in {
                "cancelada",
                "cancelled",
                "rechazada",
                "rejected",
            }:
                product_sales[item.product.name] += item.quantity or 0

        # Sort by quantity desc and take top 5
        sorted_products = sorted(
            product_sales.items(), key=lambda x: x[1], reverse=True
        )[:5]

        categories = [p[0] for p in sorted_products]
        data = [p[1] for p in sorted_products]

        return {
            "categories": categories,
            "series": [{"name": "Unidades vendidas", "data": data}],
        }

    @staticmethod
    def get_active_production_orders(assigned_user_id: int | None = None) -> list:
        active_statuses = ["pendiente", "en_proceso", "pending", "in_progress"]
        query = ProductionOrder.query.filter(
            ProductionOrder.status.in_(active_statuses)
        )
        if assigned_user_id is not None:
            query = query.filter(ProductionOrder.assigned_user_id == assigned_user_id)

        orders = query.order_by(ProductionOrder.scheduled_date.asc()).limit(10).all()
        return orders

    @staticmethod
    def get_low_stock_alerts() -> list:
        return (
            RawMaterial.query.filter(
                RawMaterial.stock <= RawMaterial.minimum_stock,
                RawMaterial.status == "active",
            )
            .order_by(RawMaterial.stock.asc())
            .all()
        )

    @staticmethod
    def get_full_dashboard(assigned_user_id: int | None = None) -> dict:
        today = date.today()
        return {
            "sales_kpi": DashboardService.get_daily_sales_kpi(today),
            "production_kpi": DashboardService.get_production_kpi(),
            "inventory_kpi": DashboardService.get_inventory_kpi(),
            "profit_kpi": DashboardService.get_profit_kpi(today),
            "weekly_sales_chart": DashboardService.get_weekly_sales_chart(today),
            "top_products_chart": DashboardService.get_top_products_chart(today),
            "active_production_orders": DashboardService.get_active_production_orders(
                assigned_user_id=assigned_user_id
            ),
            "low_stock_alerts": DashboardService.get_low_stock_alerts(),
        }
