"""Seed idempotente de BOM inicial por producto."""

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Bom, Product, RawMaterial
from app.production.services import ProductionService
from seed_dataset import BOM_TEMPLATES, PRODUCTS, RAW_MATERIALS
from seed_pricing_rules import (
    PriceQuote,
    build_material_catalog,
    build_price_quote,
    load_images_by_sku,
)

BOM_VERSION = "v1"


def _materials_required() -> set[str]:
    required: set[str] = set()
    for template in BOM_TEMPLATES.values():
        for item in template:
            required.add(item["raw_material"])
    return required


def _build_product_index() -> dict[str, Product]:
    skus = [product["sku"] for product in PRODUCTS]
    products = Product.query.filter(Product.sku.in_(skus)).all()
    return {product.sku: product for product in products}


def _build_material_index() -> dict[str, RawMaterial]:
    names = list(_materials_required())
    materials = RawMaterial.query.filter(RawMaterial.name.in_(names)).all()
    return {material.name: material for material in materials}


def _build_price_quotes_for_bom() -> dict[str, PriceQuote]:
    images_by_sku = load_images_by_sku()
    material_catalog = build_material_catalog(RAW_MATERIALS)

    quotes_by_sku: dict[str, PriceQuote] = {}
    errors: list[str] = []

    for product_data in PRODUCTS:
        template_name = product_data.get("bom_template")
        template = BOM_TEMPLATES.get(template_name)
        if not template:
            errors.append(
                f"{product_data['sku']}: no se encontro bom_template '{template_name}'"
            )
            continue

        try:
            quote = build_price_quote(
                product_data=product_data,
                base_template=template,
                image_urls=images_by_sku.get(product_data["sku"], []),
                material_catalog=material_catalog,
            )
            quotes_by_sku[product_data["sku"]] = quote
        except Exception as exc:
            errors.append(f"{product_data['sku']}: {exc}")

    if errors:
        joined_errors = "\n- ".join(errors)
        raise RuntimeError(
            "No se puede sembrar BOM por inconsistencias visual-material:\n"
            f"- {joined_errors}"
        )

    return quotes_by_sku


def seed_bom() -> None:
    app = create_app()
    with app.app_context():
        product_index = _build_product_index()
        material_index = _build_material_index()
        price_quotes = _build_price_quotes_for_bom()

        created = 0
        updated = 0
        skipped = 0

        for product_data in PRODUCTS:
            sku = product_data["sku"]
            product = product_index.get(sku)
            if not product:
                print(f"  ⚠️ Producto no encontrado para BOM: {sku}")
                skipped += 1
                continue

            template_name = product_data.get("bom_template")
            quote = price_quotes.get(sku)
            if quote is None:
                print(f"  ⚠️ Sin cotizacion visual para {sku}")
                skipped += 1
                continue

            items_data = []
            missing_materials = []
            for item in quote.adjusted_template:
                material = material_index.get(item["raw_material"])
                if not material:
                    missing_materials.append(item["raw_material"])
                    continue

                items_data.append(
                    {
                        "raw_material_id": material.id,
                        "quantity_required": item["quantity_required"],
                    }
                )

            if missing_materials:
                print(
                    f"  ⚠️ Materias primas faltantes para {sku}: "
                    f"{', '.join(missing_materials)}"
                )
                skipped += 1
                continue

            description = (
                f"BOM semilla {template_name} | "
                f"referencia de madera: {product_data.get('wood_type', 'N/A')}"
            )

            existing = Bom.query.filter_by(
                product_id=product.id,
                version=BOM_VERSION,
            ).first()

            try:
                if existing:
                    ProductionService.update_bom(
                        bom_id=existing.id,
                        version=BOM_VERSION,
                        description=description,
                        items_data=items_data,
                        user_id=None,
                    )
                    updated += 1
                    print(f"  ♻️ BOM actualizado: {sku} ({template_name})")
                else:
                    ProductionService.create_bom(
                        product_id=product.id,
                        version=BOM_VERSION,
                        description=description,
                        items_data=items_data,
                        user_id=None,
                    )
                    created += 1
                    print(
                        f"  ✅ BOM creado: {sku} ({template_name}) "
                        f"precio_objetivo=${quote.sale_price:,.2f}"
                    )
            except Exception as exc:
                print(f"  ❌ Error BOM {sku}: {exc}")
                skipped += 1

        print("\nSeed de BOM ejecutado.")
        print(f"- BOM creados: {created}")
        print(f"- BOM actualizados: {updated}")
        print(f"- Productos omitidos: {skipped}\n")


if __name__ == "__main__":
    seed_bom()
