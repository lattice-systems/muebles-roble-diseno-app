import csv
from datetime import datetime
from io import StringIO

from flask import flash, make_response, redirect, render_template, request, url_for
from flask_security import auth_required

from app.costs import costs_bp
from app.costs.services import CostService
from app.exceptions import NotFoundError


def _money(value) -> str:
    if value is None:
        return "N/D"
    return f"{float(value):.2f}"


def _number(value) -> str:
    if value is None:
        return "N/D"
    return f"{float(value):.3f}"


@costs_bp.route("/", methods=["GET"])
@auth_required()
def index():
    # Generar snapshot de costos si ha habido cambios
    CostService.generate_snapshot_if_changed()
    
    search_term = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    result = CostService.get_cost_rows(
        search_term=search_term or None,
        page=page,
        per_page=10,
    )

    return render_template(
        "admin/costs/index.html",
        costs=result["items"],
        pagination=result["pagination"],
        search_term=search_term,
    )


@costs_bp.route("/bulk-action", methods=["POST"])
@auth_required()
def bulk_action_costs():
    action = (request.form.get("action") or "").strip().lower()
    selected_ids_raw = (request.form.get("selected_ids") or "").strip()
    search_term = (request.form.get("q") or "").strip()
    page = request.form.get("page", 1, type=int)

    if action != "export":
        flash("Acción no válida.", "error")
        return redirect(url_for("costs.index", q=search_term, page=page))

    if not selected_ids_raw:
        flash("Selecciona al menos un producto para exportar.", "error")
        return redirect(url_for("costs.index", q=search_term, page=page))

    selected_ids = []
    for value in selected_ids_raw.split(","):
        value = value.strip()
        if value.isdigit():
            selected_ids.append(int(value))

    if not selected_ids:
        flash("No se recibieron productos válidos para exportar.", "error")
        return redirect(url_for("costs.index", q=search_term, page=page))

    rows = CostService.get_cost_rows_by_ids(selected_ids)

    if not rows:
        flash("No se encontraron productos para exportar.", "error")
        return redirect(url_for("costs.index", q=search_term, page=page))

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "Producto",
            "SKU",
            "Versión de receta",
            "Costo material",
            "Costo total",
            "Precio venta",
            "Costo unitario",
            "Margen $",
            "Margen %",
            "Estado",
        ]
    )

    for item in rows:
        writer.writerow(
            [
                item["product_name"],
                item["sku"],
                item["recipe_version"],
                _money(item["material_cost"]),
                _money(item["total_cost"]),
                _money(item["sale_price"]),
                _money(item["unit_cost"]),
                _money(item["margin_value"]),
                _money(item["margin_percentage"]),
                item["status"]["label"],
            ]
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=costos_seleccionados_{timestamp}.csv"
    )
    return response


@costs_bp.route("/export-list", methods=["GET"])
@auth_required()
def export_list_csv():
    search_term = request.args.get("q", "").strip()

    result = CostService.get_cost_rows(
        search_term=search_term or None,
        page=1,
        per_page=100000,
    )

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "Producto",
            "SKU",
            "Costo material",
            "Costo total",
            "Precio venta",
            "Margen $",
            "Margen %",
            "Estado",
        ]
    )

    for item in result["items"]:
        writer.writerow(
            [
                item["product_name"],
                item["sku"],
                _money(item["material_cost"]),
                _money(item["total_cost"]),
                _money(item["sale_price"]),
                _money(item["margin_value"]),
                _money(item["margin_percentage"]),
                item["status"]["label"],
            ]
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=costos_listado_{timestamp}.csv"
    )
    return response


@costs_bp.route("/<int:product_id>/details", methods=["GET"])
@auth_required()
def details(product_id: int):
    try:
        detail = CostService.get_product_cost_detail(product_id)
    except NotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("costs.index"))

    return render_template(
        "admin/costs/details.html",
        detail=detail,
    )


@costs_bp.route("/<int:product_id>/export", methods=["POST"])
@auth_required()
def export_cost_csv(product_id: int):
    try:
        detail = CostService.get_product_cost_detail(product_id)
    except NotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("costs.index"))

    product = detail["product"]
    summary = detail["summary"]
    latest_production = detail["latest_production"]

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Producto", product.name])
    writer.writerow(["SKU", product.sku])
    writer.writerow(["Version de receta", summary["recipe_version"]])
    writer.writerow(["Costo material", _money(summary["material_cost"])])
    writer.writerow(["Costo total", _money(summary["total_cost"])])
    writer.writerow(["Precio venta", _money(summary["sale_price"])])
    writer.writerow(["Costo unitario", _money(summary["unit_cost"])])
    writer.writerow(["Margen $", _money(summary["margin_value"])])
    writer.writerow(["Margen %", _money(summary["margin_percentage"])])
    writer.writerow(["Estado", summary["status"]["label"]])

    if latest_production:
        writer.writerow(["Orden produccion", latest_production.id])
        writer.writerow(
            [
                "Fecha produccion",
                (
                    latest_production.scheduled_date.isoformat()
                    if latest_production.scheduled_date
                    else ""
                ),
            ]
        )
        writer.writerow(["Cantidad producida", latest_production.quantity])
        writer.writerow(["Estado produccion", latest_production.status])
    else:
        writer.writerow(["Orden produccion", "Sin produccion finalizada"])

    writer.writerow([])
    writer.writerow(
        [
            "Material",
            "Cantidad requerida",
            "Unidad",
            "Merma %",
            "Costo unitario",
            "Subtotal",
        ]
    )

    for item in detail["detail_items"]:
        writer.writerow(
            [
                item["material_name"],
                _number(item["quantity_required"]),
                item["unit_abbreviation"] or item["unit_name"],
                _number(item["waste_percentage"]),
                _money(item["unit_price"]),
                _money(item["line_total"]),
            ]
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=costos_producto_{product.id}_{timestamp}.csv"
    )
    return response
