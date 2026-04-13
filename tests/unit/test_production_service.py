"""Pruebas unitarias para ProductionService en órdenes especiales."""

from datetime import date, timedelta
from decimal import Decimal

from app.models.material_category import MaterialCategory
from app.models.production_order_material import ProductionOrderMaterial
from app.models.raw_material import RawMaterial
from app.models.unit_of_measure import UnitOfMeasure
from app.production.services import ProductionService


def _build_raw_material(db_session):
    unit = UnitOfMeasure(name="Kilogramo", abbreviation="kg", type="peso", status=True)
    db_session.add(unit)
    db_session.flush()

    category = MaterialCategory(name="Insumos especiales", status="active")
    db_session.add(category)
    db_session.flush()

    raw_material = RawMaterial(
        name="Resina especial",
        description="Insumo para pedidos personalizados",
        category_id=category.id,
        unit_id=unit.id,
        waste_percentage=Decimal("3.00"),
        stock=Decimal("100.000"),
        minimum_stock=Decimal("5.000"),
        status="active",
    )
    db_session.add(raw_material)
    db_session.commit()

    return raw_material


class TestSpecialProductionOrderMaterials:
    """Valida captura de materiales en órdenes especiales."""

    def test_special_order_allows_manual_material_rows_after_start(
        self, app, db_session, seed_basic_data
    ):
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]
        raw_material = _build_raw_material(db_session)

        order = ProductionService.create_production_order(
            product_id=product.id,
            quantity=1,
            scheduled_date=date.today() + timedelta(days=5),
            user_id=user.id,
            is_special_request=True,
            do_not_add_to_finished_stock=True,
        )

        ProductionService.change_production_order_status(
            production_order_id=order.id,
            new_status="en_proceso",
            user_id=user.id,
        )

        ProductionService.update_material_usage(
            production_order_id=order.id,
            materials_data=[
                {
                    "raw_material_id": str(raw_material.id),
                    "quantity_planned": "2.500",
                    "quantity_used": "2.250",
                    "waste_applied": "4.50",
                }
            ],
            user_id=user.id,
        )

        created_row = ProductionOrderMaterial.query.filter_by(
            production_order_id=order.id,
            raw_material_id=raw_material.id,
        ).first()

        assert created_row is not None
        assert created_row.quantity_planned == Decimal("2.500")
        assert created_row.quantity_used == Decimal("2.250")
        assert created_row.waste_applied == Decimal("4.50")

    def test_special_order_can_initialize_materials_from_bom_after_start(
        self, app, db_session, seed_basic_data
    ):
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]
        raw_material = _build_raw_material(db_session)

        order = ProductionService.create_production_order(
            product_id=product.id,
            quantity=2,
            scheduled_date=date.today() + timedelta(days=7),
            user_id=user.id,
            is_special_request=True,
            do_not_add_to_finished_stock=True,
        )

        ProductionService.change_production_order_status(
            production_order_id=order.id,
            new_status="en_proceso",
            user_id=user.id,
        )

        ProductionService.create_bom(
            product_id=product.id,
            version="v-especial-1",
            description="BOM especial registrada después de iniciar",
            items_data=[
                {
                    "raw_material_id": str(raw_material.id),
                    "quantity_required": "1.250",
                }
            ],
            user_id=user.id,
        )

        materials = ProductionService.initialize_material_plan(
            production_order_id=order.id,
            user_id=user.id,
        )

        assert len(materials) == 1
        assert materials[0].quantity_planned == Decimal("2.500")
        assert materials[0].raw_material_id == raw_material.id
