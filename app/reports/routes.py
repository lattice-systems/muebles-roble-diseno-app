import csv
from datetime import date
from io import StringIO

from flask import flash, make_response, redirect, render_template, url_for
from flask_security import auth_required

from app.reports import reports_bp
from app.reports.services import ReportService


@reports_bp.route("/", methods=["GET"])
@auth_required()
def index():
    dashboard = ReportService.get_dashboard(target_date=date.today())
    return render_template(
        "admin/reports/index.html",
        dashboard=dashboard,
    )


@reports_bp.route("/refresh", methods=["POST"])
@auth_required()
def refresh():
    ReportService.refresh_dashboard_snapshots(date.today())
    flash("Reportes regenerados correctamente.", "success")
    return redirect(url_for("reports.index"))


@reports_bp.route("/sales-details", methods=["GET"])
@auth_required()
def sales_details():
    dashboard = ReportService.get_dashboard(target_date=date.today())
    return render_template(
        "admin/reports/sales_details.html",
        weekly=dashboard["weekly_sales"],
        recent=dashboard["recent_sales"],
        sales=dashboard["daily_sales"],
    )


@reports_bp.route("/top-products-details", methods=["GET"])
@auth_required()
def top_products_details():
    dashboard = ReportService.get_dashboard(target_date=date.today())
    return render_template(
        "admin/reports/top_products_details.html",
        top_products=dashboard["top_products"],
    )


@reports_bp.route("/raw-material-consumption", methods=["GET"])
@auth_required()
def raw_material_consumption_details():
    data = ReportService.get_raw_material_consumption_report()
    return render_template(
        "admin/reports/raw_material_consumption.html",
        report=data,
    )


@reports_bp.route("/general-report", methods=["GET"])
@auth_required()
def general_report_details():
    data = ReportService.get_general_report()
    return render_template(
        "admin/reports/general_report.html",
        report=data,
    )


@reports_bp.route("/export/daily-cut.csv", methods=["GET"])
@auth_required()
def export_daily_cut_csv():
    report = ReportService.get_dashboard(target_date=date.today())["daily_sales"]

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Fecha", report["report_date"]])
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
    response.headers["Content-Disposition"] = "attachment; filename=corte_diario.csv"
    return response