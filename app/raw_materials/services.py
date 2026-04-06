from __future__ import annotations

from typing import Optional

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models import RawMaterial, RawMaterialMovement
from app.shared.audit_logging import log_application_audit


class RawMaterialService:
    """Lógica de negocio para Materia Prima."""

    @staticmethod
    def _log_audit(
        action: str, previous: dict | None = None, new: dict | None = None
    ) -> None:
        """Helper para crear auditoria de aplicacion (fallback fuera de MySQL)."""
        log_application_audit(
            table_name="raw_materials",
            action=action,
            previous_data=previous,
            new_data=new,
        )

    @staticmethod
    def get_all(
        search_term: Optional[str] = None,
        status_filter: str = "all",
        page: int = 1,
        per_page: int = 10,
    ):
        query = RawMaterial.query

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(RawMaterial.name.ilike(term))

        if status_filter in ["active", "inactive"]:
            query = query.filter_by(status=status_filter)

        return query.order_by(RawMaterial.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_by_id(raw_material_id: int) -> RawMaterial:
        raw_material = db.session.get(RawMaterial, raw_material_id)
        if not raw_material:
            raise NotFoundError("Materia prima no encontrada.")
        return raw_material

    @staticmethod
    def get_by_ids(ids: list[int]) -> list[RawMaterial]:
        if not ids:
            return []
        return RawMaterial.query.filter(RawMaterial.id.in_(ids)).all()

    @staticmethod
    def create(data: dict) -> RawMaterial:
        if RawMaterial.query.filter_by(name=data["name"]).first():
            raise ConflictError("Ya existe una materia prima con este nombre.")

        try:
            raw_material = RawMaterial(
                name=data["name"],
                description=data.get("description", ""),
                category_id=data["category_id"],
                unit_id=data["unit_id"],
                waste_percentage=data.get("waste_percentage", 0.0),
                status=data.get("status", "active"),
                stock=0.0,  # El stock siempre inicia en 0 y se modifica via auditoría
            )

            db.session.add(raw_material)
            db.session.flush()

            RawMaterialService._log_audit(
                action="create",
                previous=None,
                new={
                    "id": raw_material.id,
                    "name": raw_material.name,
                    "status": raw_material.status,
                    "waste_percentage": float(raw_material.waste_percentage),
                },
            )
            db.session.commit()
            return raw_material

        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"Error creando la materia prima: {str(e)}")

    @staticmethod
    def update(raw_material_id: int, data: dict) -> RawMaterial:
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        # Checar que el nuevo nombre no choque con otro
        existing = RawMaterial.query.filter_by(name=data["name"]).first()
        if existing and existing.id != raw_material_id:
            raise ConflictError("Ya existe otra materia prima con este nombre.")

        try:
            old_status = raw_material.status
            new_status = data.get("status", raw_material.status)

            raw_material.name = data["name"]
            raw_material.description = data.get("description", "")
            raw_material.category_id = data["category_id"]
            raw_material.unit_id = data["unit_id"]
            raw_material.waste_percentage = data.get(
                "waste_percentage", raw_material.waste_percentage
            )
            raw_material.status = new_status

            RawMaterialService._log_audit(
                action="update",
                previous={"status": old_status},
                new={"status": new_status, "name": raw_material.name},
            )
            db.session.commit()
            return raw_material

        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"Error actualizando la materia prima: {str(e)}")

    @staticmethod
    def toggle_status(raw_material_id: int) -> bool:
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        try:
            new_status = "active" if raw_material.status == "inactive" else "inactive"
            action = "activate" if new_status == "active" else "deactivate"

            RawMaterialService._log_audit(
                action=action,
                previous={"status": raw_material.status},
                new={
                    "status": new_status,
                    "id": raw_material.id,
                    "name": raw_material.name,
                },
            )

            raw_material.status = new_status

            db.session.commit()
            return new_status == "active"

        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"Error al cambiar el estado: {str(e)}")

    @staticmethod
    def bulk_set_status(ids: list[int], target_status: bool) -> dict:
        if not ids:
            return {"updated": 0, "not_found": 0}

        status_value = "active" if target_status else "inactive"
        action = "bulk_activate" if target_status else "bulk_deactivate"

        try:
            raw_materials = RawMaterialService.get_by_ids(ids)
            found_ids = [rm.id for rm in raw_materials]

            # Solo actualizar los que necesitan cambio
            to_update = [rm for rm in raw_materials if rm.status != status_value]
            updated_count = len(to_update)

            for rm in to_update:
                old_status = rm.status
                rm.status = status_value
                RawMaterialService._log_audit(
                    action=action,
                    previous={"status": old_status},
                    new={"status": status_value, "id": rm.id, "name": rm.name},
                )

            if updated_count > 0:
                db.session.commit()

            return {"updated": updated_count, "not_found": len(ids) - len(found_ids)}
        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"Error procesando acciones masivas: {str(e)}")

    @staticmethod
    def adjust_stock(
        raw_material_id: int,
        movement_type: str,
        quantity: float,
        reason: str,
        reference: str = "",
    ) -> RawMaterial:
        """
        Ajusta el inventario manual o sistemáticamente dejando un rastro auditable (Movimiento).
        :param raw_material_id: ID de la materia prima.
        :param movement_type: ENTRADA | MERMA | AJUSTE_ENTRADA | AJUSTE_SALIDA | PRODUCCION
        :param quantity: Cantidad (absoluta positiva).
        :param reason: Razón detallada obligatoria.
        :param reference: Campo extra (e.g. número de OC o Factura).
        """
        raw_material = RawMaterialService.get_by_id(raw_material_id)

        try:
            qty_decimal = float(quantity)
            if qty_decimal <= 0:
                raise ValidationError("La cantidad a ajustar debe ser mayor a 0.")

            if not reason or not reason.strip():
                raise ValidationError("El motivo del ajuste es obligatorio.")

            movement = RawMaterialMovement(
                raw_material_id=raw_material.id,
                movement_type=movement_type.upper(),
                quantity=qty_decimal,
                reason=reason.strip(),
                reference=reference,
            )
            db.session.add(movement)

            es_entrada = movement_type.upper() in ["ENTRADA", "AJUSTE_ENTRADA"]
            if es_entrada:
                raw_material.stock = float(raw_material.stock) + qty_decimal
            else:
                # Salida, merma o producción
                if float(raw_material.stock) < qty_decimal:
                    raise ConflictError(
                        f"Stock insuficiente para {raw_material.name}. Tienes {raw_material.stock} y quieres sacar {qty_decimal}."
                    )
                raw_material.stock = float(raw_material.stock) - qty_decimal

            RawMaterialService._log_audit(
                action="stock_adjustment",
                previous={
                    "stock": (
                        float(raw_material.stock) - qty_decimal
                        if es_entrada
                        else float(raw_material.stock) + qty_decimal
                    )
                },
                new={
                    "stock": float(raw_material.stock),
                    "reason": reason,
                    "movement_type": movement_type,
                    "id": raw_material.id,
                },
            )

            db.session.commit()
            return raw_material

        except ConflictError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise ValidationError(f"Error ajustando inventario: {str(e)}")

    @staticmethod
    def get_stock_movements(raw_material_id: int, page: int = 1, per_page: int = 20):
        # Valida existencia
        RawMaterialService.get_by_id(raw_material_id)

        return (
            RawMaterialMovement.query.filter_by(raw_material_id=raw_material_id)
            .order_by(
                RawMaterialMovement.created_at.desc(), RawMaterialMovement.id.desc()
            )
            .paginate(page=page, per_page=per_page, error_out=False)
        )
