"""Pruebas unitarias para ProductionService en órdenes especiales."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.exceptions import ValidationError
from app.models.material_category import MaterialCategory
from app.models.role import Role
from app.models.production_order_material import ProductionOrderMaterial
from app.models.raw_material import RawMaterial
from app.models.unit_of_measure import UnitOfMeasure
from app.models.user import User
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

        ProductionService.create_bom(
            product_id=product.id,
            version="v-especial-manual-1",
            description="BOM requerida para iniciar producción especial",
            items_data=[
                {
                    "raw_material_id": str(raw_material.id),
                    "quantity_required": "2.500",
                }
            ],
            user_id=user.id,
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

    def test_special_order_cannot_start_without_bom_and_then_can_initialize(
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

        with pytest.raises(ValidationError, match="no tiene una receta BOM"):
            ProductionService.change_production_order_status(
                production_order_id=order.id,
                new_status="en_proceso",
                user_id=user.id,
            )

        ProductionService.create_bom(
            product_id=product.id,
            version="v-especial-1",
            description="BOM especial requerida para iniciar producción",
            items_data=[
                {
                    "raw_material_id": str(raw_material.id),
                    "quantity_required": "1.250",
                }
            ],
            user_id=user.id,
        )

        ProductionService.change_production_order_status(
            production_order_id=order.id,
            new_status="en_proceso",
            user_id=user.id,
        )

        materials = ProductionService.initialize_material_plan(
            production_order_id=order.id,
            user_id=user.id,
        )

        assert len(materials) == 1
        assert materials[0].quantity_planned == Decimal("2.500")
        assert materials[0].raw_material_id == raw_material.id


class TestProductionOrderAssignee:
    """Valida reglas de asignación de responsables de producción."""

    def test_create_order_stores_assigned_user(self, app, db_session, seed_basic_data):
        product = seed_basic_data["product"]
        user = seed_basic_data["user"]

        order = ProductionService.create_production_order(
            product_id=product.id,
            quantity=1,
            scheduled_date=date.today() + timedelta(days=3),
            user_id=user.id,
            assigned_user_id=user.id,
            is_special_request=True,
            do_not_add_to_finished_stock=True,
        )

        assert order.assigned_user_id == user.id

    def test_create_order_rejects_non_allowed_role_assignee(
        self, app, db_session, seed_basic_data
    ):
        product = seed_basic_data["product"]
        admin_user = seed_basic_data["user"]

        sales_role = Role(name="sales", description="Ventas", status=True)
        db_session.add(sales_role)
        db_session.flush()

        sales_user = User(
            full_name="Usuario Ventas",
            email="sales@test.com",
            password_hash="hashed_password_placeholder",
            role_id=sales_role.id,
            status=True,
        )
        db_session.add(sales_user)
        db_session.commit()

        with pytest.raises(ValidationError, match="Solo se puede asignar"):
            ProductionService.create_production_order(
                product_id=product.id,
                quantity=1,
                scheduled_date=date.today() + timedelta(days=4),
                user_id=admin_user.id,
                assigned_user_id=sales_user.id,
                is_special_request=True,
                do_not_add_to_finished_stock=True,
            )

    def test_assign_order_allows_reassignment_to_production_role(
        self, app, db_session, seed_basic_data
    ):
        product = seed_basic_data["product"]
        admin_user = seed_basic_data["user"]

        production_role = Role(name="production", description="Producción", status=True)
        db_session.add(production_role)
        db_session.flush()

        production_user = User(
            full_name="Usuario Producción",
            email="production@test.com",
            password_hash="hashed_password_placeholder",
            role_id=production_role.id,
            status=True,
        )
        db_session.add(production_user)
        db_session.commit()

        order = ProductionService.create_production_order(
            product_id=product.id,
            quantity=1,
            scheduled_date=date.today() + timedelta(days=5),
            user_id=admin_user.id,
            assigned_user_id=admin_user.id,
            is_special_request=True,
            do_not_add_to_finished_stock=True,
        )

        updated_order = ProductionService.assign_production_order(
            production_order_id=order.id,
            assigned_user_id=production_user.id,
            user_id=admin_user.id,
        )

        assert updated_order.assigned_user_id == production_user.id
