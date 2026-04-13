import csv
from datetime import date, datetime, timedelta
from io import StringIO
from math import ceil

from flask import flash, make_response, redirect, render_template, request, url_for
from flask_security import auth_required

from app.reports import reports_bp
from app.reports.services import ReportService
from app.dashboard.services import DashboardService


class SimplePagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = ceil(total / per_page) if per_page else 0

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


def _parse_date(value: str | None, default: date | None = None) -> date | None:
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return default


def _resolve_date_range():
    today = date.today()
    default_date_from = today - timedelta(days=29)
    default_date_to = today

    date_from = _parse_date(request.args.get("date_from"), default_date_from)
    date_to = _parse_date(request.args.get("date_to"), default_date_to)

    if date_from is None:
        date_from = default_date_from
    if date_to is None:
        date_to = default_date_to

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    return date_from, date_to


@reports_bp.route("/", methods=["GET"])
@auth_required()
def index():
    page = request.args.get("page", 1, type=int)
    search_term = request.args.get("q", "", type=str).strip()
    source_filter = request.args.get("source", "all", type=str)
    date_from, date_to = _resolve_date_range()

    target_date = date_to

    dashboard = ReportService.get_dashboard(target_date=target_date)
    weekly_sales = dashboard.get("weekly_sales") if dashboard else None
    if (
        not weekly_sales
        or not isinstance(weekly_sales.get("items"), list)
        or len(weekly_sales.get("items", [])) != 7
        or "max_amount" not in weekly_sales
    ):
        dashboard = ReportService.get_dashboard(target_date=target_date, force_refresh=True)

    # Get chart data for ApexCharts
    weekly_sales_chart = DashboardService.get_weekly_sales_chart(target_date=target_date)

    comparison_metrics = ReportService.get_dashboard_comparison_metrics(
        target_date=target_date
    )

    recent_items = ReportService.get_recent_sales_rows(
        date_from=date_from,
        date_to=date_to,
        search_term=search_term,
        source_filter=source_filter,
    )

    per_page = 10
    total = len(recent_items)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = recent_items[start:end]

    pagination = SimplePagination(
        items=paginated_items,
        page=page,
        per_page=per_page,
        total=total,
    )

    general_report = ReportService.get_general_report(
        date_from=date_from,
        date_to=date_to,
    )

    return render_template(
        "admin/reports/index.html",
        dashboard=dashboard,
        weekly_sales_chart=weekly_sales_chart,
        general_report=general_report,
        comparison_metrics=comparison_metrics,
        pagination=pagination,
        search_term=search_term,
        source_filter=source_filter,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
    )


@reports_bp.route("/refresh", methods=["POST"])
@auth_required()
def refresh():
    date_from = _parse_date(request.form.get("date_from"), date.today())
    date_to = _parse_date(request.form.get("date_to"), date.today())

    if date_from is None:
        date_from = date.today()
    if date_to is None:
        date_to = date.today()

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    ReportService.refresh_dashboard_snapshots(date_to)
    flash("Reportes regenerados correctamente.", "success")
    return redirect(
        url_for(
            "reports.index",
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
        )
    )


@reports_bp.route("/sales-details", methods=["GET"])
@auth_required()
def sales_details():
    date_from, date_to = _resolve_date_range()
    target_date = date_to

    dashboard = ReportService.get_dashboard(target_date=target_date)
    weekly_sales = dashboard.get("weekly_sales") if dashboard else None
    if (
        not weekly_sales
        or not isinstance(weekly_sales.get("items"), list)
        or len(weekly_sales.get("items", [])) != 7
        or "max_amount" not in weekly_sales
    ):
        dashboard = ReportService.get_dashboard(target_date=target_date, force_refresh=True)

    recent = ReportService.get_recent_sales_rows(date_from=date_from, date_to=date_to)

    return render_template(
        "admin/reports/sales_details.html",
        weekly=dashboard["weekly_sales"],
        recent={"items": recent},
        sales=ReportService.get_general_report(date_from=date_from, date_to=date_to)[
            "sales"
        ],
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
    )


@reports_bp.route("/top-products-details", methods=["GET"])
@auth_required()
def top_products_details():
    date_from, date_to = _resolve_date_range()
    top_products = ReportService.generate_top_products_snapshot(
        date_from=date_from,
        date_to=date_to,
    )

    return render_template(
        "admin/reports/top_products_details.html",
        top_products=top_products,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
    )


@reports_bp.route("/raw-material-consumption", methods=["GET"])
@auth_required()
def raw_material_consumption_details():
    date_from, date_to = _resolve_date_range()
    data = ReportService.get_raw_material_consumption_report(
        date_from=date_from,
        date_to=date_to,
    )

    return render_template(
        "admin/reports/raw_material_consumption.html",
        report=data,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
    )


@reports_bp.route("/general-report", methods=["GET"])
@auth_required()
def general_report_details():
    date_from, date_to = _resolve_date_range()
    data = ReportService.get_general_report(date_from=date_from, date_to=date_to)

    return render_template(
        "admin/reports/general_report.html",
        report=data,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
    )


@reports_bp.route("/export/daily-cut.csv", methods=["GET"])
@auth_required()
def export_daily_cut_csv():
    date_from, date_to = _resolve_date_range()
    report = ReportService.get_general_report(date_from=date_from, date_to=date_to)[
        "sales"
    ]

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Fecha inicio", date_from.isoformat()])
    writer.writerow(["Fecha fin", date_to.isoformat()])
    writer.writerow(["POS", report["totals"]["pos_sales"]])
    writer.writerow(["E-commerce", report["totals"]["ecommerce_sales"]])
    writer.writerow(["Total", report["totals"]["grand_total"]])
    writer.writerow(["Transacciones", report["totals"]["transactions_count"]])
    writer.writerow([])
    writer.writerow(["Método", "Monto", "Cantidad"])

    for item in report["payment_methods"]:
        writer.writerow([item["method"], item["amount"], item["count"]])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=corte_periodo.csv"
    return response


@reports_bp.route("/bulk-action", methods=["POST"])
@auth_required()
def bulk_action_reports():
    action = request.form.get("action", "").strip()
    selected_ids_raw = request.form.get("selected_ids", "").strip()

    search_term = request.form.get("q", "", type=str)
    source_filter = request.form.get("source", "all", type=str)
    page = request.form.get("page", 1, type=int)

    date_from = _parse_date(
        request.form.get("date_from"),
        date.today() - timedelta(days=29),
    )
    date_to = _parse_date(request.form.get("date_to"), date.today())

    if date_from is None:
        date_from = date.today() - timedelta(days=29)
    if date_to is None:
        date_to = date.today()

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    if not selected_ids_raw:
        flash("No se seleccionó ninguna venta.", "warning")
        return redirect(
            url_for(
                "reports.index",
                page=page,
                q=search_term,
                source=source_filter,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        )

    selected_keys = [
        value.strip() for value in selected_ids_raw.split(",") if value.strip()
    ]

    if not selected_keys:
        flash("No se seleccionó ninguna venta válida.", "warning")
        return redirect(
            url_for(
                "reports.index",
                page=page,
                q=search_term,
                source=source_filter,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        )

    if action != "export":
        flash("La acción solicitada no es válida.", "danger")
        return redirect(
            url_for(
                "reports.index",
                page=page,
                q=search_term,
                source=source_filter,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        )

    rows = ReportService.get_recent_sales_rows(
        date_from=date_from,
        date_to=date_to,
        search_term=search_term,
        source_filter=source_filter,
    )

    selected_rows = [row for row in rows if row["row_id"] in selected_keys]

    if not selected_rows:
        flash("No se encontraron ventas para exportar.", "warning")
        return redirect(
            url_for(
                "reports.index",
                page=page,
                q=search_term,
                source=source_filter,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Venta", "Fecha", "Origen", "Método de pago", "Subtotal", "IVA", "Total"]
    )

    for item in selected_rows:
        writer.writerow(
            [
                item["label"],
                item["date"],
                item["source"],
                item["payment_method"],
                item["subtotal"],
                item["iva"],
                item["total"],
            ]
        )

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=ventas_seleccionadas.csv"
    )
    return response


@reports_bp.route("/export/recent-sale/<string:row_id>", methods=["GET"])
@auth_required()
def export_recent_sale(row_id):
    date_from, date_to = _resolve_date_range()

    rows = ReportService.get_recent_sales_rows(date_from=date_from, date_to=date_to)
    item = next((row for row in rows if row["row_id"] == row_id), None)

    if not item:
        flash("No se encontró la venta solicitada.", "warning")
        return redirect(
            url_for(
                "reports.index",
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Venta", "Fecha", "Origen", "Método de pago", "Subtotal", "IVA", "Total"]
    )
    writer.writerow(
        [
            item["label"],
            item["date"],
            item["source"],
            item["payment_method"],
            item["subtotal"],
            item["iva"],
            item["total"],
        ]
    )

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename={item['label'].replace('#', '_')}.csv"
    )
    return response
