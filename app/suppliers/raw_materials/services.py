from sqlalchemy.exc import IntegrityError

from ...exceptions import ConflictError, NotFoundError, ValidationError
from ...extensions import db
from ...models.material_category import MaterialCategory
from ...models.raw_material import RawMaterial
from ...models.raw_material_movement import RawMaterialMovement
from ...models.supplier import Supplier
from ...models.unit_of_measure import UnitOfMeasure


class RawMaterialService:
    @staticmethod
    def get_all() -> list[RawMaterial]:
        return RawMaterial.query.order_by(RawMaterial.name.asc()).all()

    @staticmethod
    def get_by_id(raw_material_id: int) -> RawMaterial:
        raw_material = RawMaterial.query.get(raw_material_id)
        if not raw_material:
            raise NotFoundError("La materia prima no existe.")
        return raw_material

    @staticmethod
    def create(data: dict) -> RawMaterial:
        name = data.get("name", "").strip()
        description = data.get("description")
        category_id = data.get("category_id")
        unit_id = data.get("unit_id")
        stock = data.get("stock", 0)
        estimated_cost = data.get("estimated_cost")
        waste_percentage = data.get("waste_percentage", 0)
        status = data.get("status", "active")
        supplier_id = data.get("supplier_id")

        if not name:
            raise ValidationError("El nombre es obligatorio.")

        if status not in ("active", "inactive"):
            raise ValidationError("El estado no es válido.")

        if stock is None or stock < 0:
            raise ValidationError("El stock no puede ser negativo.")

        if waste_percentage is None or waste_percentage < 0 or waste_percentage > 100:
            raise ValidationError("El porcentaje de merma debe estar entre 0 y 100.")

        if estimated_cost is not None and estimated_cost < 0:
            raise ValidationError("El costo estimado no puede ser negativo.")

        if not MaterialCategory.query.get(category_id):
            raise ValidationError("La categoría no existe.")

        if not UnitOfMeasure.query.get(unit_id):
            raise ValidationError("La unidad de medida no existe.")

        if supplier_id in (0, "0", "", None):
            supplier_id = None
        elif not Supplier.query.get(supplier_id):
            raise ValidationError("El proveedor no existe.")

        existing = RawMaterial.query.filter_by(name=name).first()
        if existing:
            raise ConflictError("Ya existe una materia prima con ese nombre.")

        raw_material = RawMaterial(
            name=name,
            description=description,
            category_id=category_id,
            unit_id=unit_id,
            stock=stock,
            estimated_cost=estimated_cost,
            waste_percentage=waste_percentage,
            status=status,
            supplier_id=supplier_id,
        )

        try:
            db.session.add(raw_material)
            db.session.commit()
            return raw_material
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("No fue posible registrar la materia prima.")

    @staticmethod
    def update(raw_material_id: int, data: dict) -> RawMaterial:
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        name = data.get("name", "").strip()
        description = data.get("description")
        category_id = data.get("category_id")
        unit_id = data.get("unit_id")
        stock = data.get("stock")
        estimated_cost = data.get("estimated_cost")
        waste_percentage = data.get("waste_percentage", 0)
        status = data.get("status", "active")
        supplier_id = data.get("supplier_id")

        if not name:
            raise ValidationError("El nombre es obligatorio.")

        if status not in ("active", "inactive"):
            raise ValidationError("El estado no es válido.")

        if stock is None or stock < 0:
            raise ValidationError("El stock no puede ser negativo.")

        if waste_percentage is None or waste_percentage < 0 or waste_percentage > 100:
            raise ValidationError("El porcentaje de merma debe estar entre 0 y 100.")

        if estimated_cost is not None and estimated_cost < 0:
            raise ValidationError("El costo estimado no puede ser negativo.")

        if not MaterialCategory.query.get(category_id):
            raise ValidationError("La categoría no existe.")

        if not UnitOfMeasure.query.get(unit_id):
            raise ValidationError("La unidad de medida no existe.")

        if supplier_id in (0, "0", "", None):
            supplier_id = None
        elif not Supplier.query.get(supplier_id):
            raise ValidationError("El proveedor no existe.")

        existing = RawMaterial.query.filter(
            RawMaterial.name == name,
            RawMaterial.id != raw_material_id,
        ).first()

        if existing:
            raise ConflictError("Ya existe una materia prima con ese nombre.")

        raw_material.name = name
        raw_material.description = description
        raw_material.category_id = category_id
        raw_material.unit_id = unit_id
        raw_material.stock = stock
        raw_material.estimated_cost = estimated_cost
        raw_material.waste_percentage = waste_percentage
        raw_material.status = status
        raw_material.supplier_id = supplier_id

        try:
            db.session.commit()
            return raw_material
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("No fue posible actualizar la materia prima.")

    @staticmethod
    def toggle_status(raw_material_id: int) -> RawMaterial:
        raw_material = RawMaterialService.get_by_id(raw_material_id)
        raw_material.status = (
            "inactive" if raw_material.status == "active" else "active"
        )

        try:
            db.session.commit()
            return raw_material
        except IntegrityError:
            db.session.rollback()
            raise ValidationError("No fue posible actualizar el estado.")

    @staticmethod
    def adjust_stock(raw_material_id: int, data: dict) -> RawMaterial:
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        movement_type = data.get("movement_type")
        quantity = data.get("quantity")
        reason = data.get("reason", "").strip()

        if movement_type not in ("ADJUSTMENT_IN", "ADJUSTMENT_OUT"):
            raise ValidationError("El tipo de movimiento no es válido.")

        if quantity is None or quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")

        if not reason:
            raise ValidationError("El motivo es obligatorio.")

        if movement_type == "ADJUSTMENT_OUT" and raw_material.stock < quantity:
            raise ValidationError("No hay stock suficiente para realizar el ajuste.")

        if movement_type == "ADJUSTMENT_IN":
            raw_material.stock += quantity
        else:
            raw_material.stock -= quantity

        movement = RawMaterialMovement(
            raw_material_id=raw_material.id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
        )

        try:
            db.session.add(movement)
            db.session.commit()
            return raw_material
        except IntegrityError:
            db.session.rollback()
            raise ValidationError("No fue posible actualizar el stock.")

    @staticmethod
    def update_waste(raw_material_id: int, data: dict) -> RawMaterial:
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        waste_percentage = data.get("waste_percentage")

        if waste_percentage is None or waste_percentage < 0 or waste_percentage > 100:
            raise ValidationError("El porcentaje de merma debe estar entre 0 y 100.")

        raw_material.waste_percentage = waste_percentage

        try:
            db.session.commit()
            return raw_material
        except IntegrityError:
            db.session.rollback()
            raise ValidationError("No fue posible actualizar la merma.")
