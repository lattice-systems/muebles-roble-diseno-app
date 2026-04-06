"""
Servicios de lógica de negocio para proveedores.
"""

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.supplier import Supplier
from app.shared.audit_logging import log_application_audit


class SupplierService:
    """Servicio para operaciones de negocio relacionadas con proveedores."""

    @staticmethod
    def _log_audit(action: str, previous: dict | None, new: dict | None) -> None:
        """Registra auditoria de aplicacion (fallback fuera de MySQL)."""
        log_application_audit(
            table_name="suppliers",
            action=action,
            previous_data=previous,
            new_data=new,
        )

    @staticmethod
    def get_by_ids(supplier_ids: list[int]) -> list[Supplier]:
        """Obtiene proveedores por una lista de IDs."""
        if not supplier_ids:
            return []

        return (
            Supplier.query.filter(Supplier.id.in_(supplier_ids))
            .order_by(Supplier.id.asc())
            .all()
        )

    @staticmethod
    def get_all(
        search_term: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """
        Obtiene proveedores con búsqueda, filtro de estado y paginación.
        """
        query = Supplier.query

        if status_filter == "active":
            query = query.filter(Supplier.status.is_(True))
        elif status_filter == "inactive":
            query = query.filter(Supplier.status.is_(False))

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    Supplier.name.ilike(term),
                    Supplier.email.ilike(term),
                    Supplier.phone.ilike(term),
                )
            )

        query = query.order_by(Supplier.id.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_by_id(id_supplier: int) -> Supplier:
        """Obtiene un proveedor por su ID."""
        supplier = db.session.get(Supplier, id_supplier)
        if not supplier:
            raise NotFoundError(f"No se encontró un proveedor con ID {id_supplier}")
        return supplier

    @staticmethod
    def create(data: dict) -> Supplier:
        """Crea un nuevo proveedor con validaciones de negocio."""
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip() or None
        email = (data.get("email") or "").strip().lower() or None
        address = (data.get("address") or "").strip() or None
        status = data.get("status", True)

        if not name:
            raise ValidationError("El nombre del proveedor es requerido")
        if len(name) > 150:
            raise ValidationError("El nombre no puede exceder 150 caracteres")
        if phone:
            if not phone.isdigit() or len(phone) != 10:
                raise ValidationError(
                    "El teléfono debe tener exactamente 10 dígitos numéricos"
                )

        existing_name = Supplier.query.filter(Supplier.name.ilike(name)).first()
        if existing_name:
            raise ConflictError(f"Ya existe un proveedor con el nombre '{name}'")

        if email:
            existing_email = Supplier.query.filter(Supplier.email.ilike(email)).first()
            if existing_email:
                raise ConflictError(f"Ya existe un proveedor con el correo '{email}'")

        if isinstance(status, str):
            status = status.lower() in {"1", "true", "on", "yes"}

        supplier = Supplier(
            name=name,
            phone=phone,
            email=email,
            address=address,
            status=bool(status),
        )

        db.session.add(supplier)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(
                "Hubo un conflicto de integridad (nombre o correo duplicado)."
            )

        SupplierService._log_audit("CREATE", None, supplier.to_dict())
        db.session.commit()

        return supplier

    @staticmethod
    def update(id_supplier: int, data: dict) -> Supplier:
        """Actualiza la información de un proveedor existente."""
        supplier = SupplierService.get_by_id(id_supplier)
        previous = supplier.to_dict()

        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip() or None
        email = (data.get("email") or "").strip().lower() or None
        address = (data.get("address") or "").strip() or None
        status = data.get("status", True)

        if not name:
            raise ValidationError("El nombre del proveedor es requerido")
        if len(name) > 150:
            raise ValidationError("El nombre no puede exceder 150 caracteres")
        if phone:
            if not phone.isdigit() or len(phone) != 10:
                raise ValidationError(
                    "El teléfono debe tener exactamente 10 dígitos numéricos"
                )

        if name.lower() != supplier.name.lower():
            existing_name = Supplier.query.filter(Supplier.name.ilike(name)).first()
            if existing_name:
                raise ConflictError(f"Ya existe un proveedor con el nombre '{name}'")

        if email and (not supplier.email or email.lower() != supplier.email.lower()):
            existing_email = Supplier.query.filter(Supplier.email.ilike(email)).first()
            if existing_email:
                raise ConflictError(f"Ya existe un proveedor con el correo '{email}'")

        if isinstance(status, str):
            status = status.lower() in {"1", "true", "on", "yes"}

        supplier.name = name
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.status = bool(status)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(
                "Hubo un conflicto de integridad (nombre o correo duplicado)."
            )

        SupplierService._log_audit("UPDATE", previous, supplier.to_dict())
        db.session.commit()

        return supplier

    @staticmethod
    def toggle_status(id_supplier: int) -> bool:
        """Alterna el estado (activo/inactivo) de un proveedor."""
        supplier = SupplierService.get_by_id(id_supplier)
        previous = supplier.to_dict()

        supplier.status = not supplier.status
        action = "ACTIVATE" if supplier.status else "DEACTIVATE"

        SupplierService._log_audit(action, previous, supplier.to_dict())
        db.session.commit()

        return supplier.status

    @staticmethod
    def bulk_set_status(supplier_ids: list[int], target_status: bool) -> dict[str, int]:
        """Actualiza estado de proveedores en lote y retorna el resumen."""
        if not supplier_ids:
            return {"updated": 0, "not_found": 0}

        unique_ids = list(dict.fromkeys(supplier_ids))
        suppliers = Supplier.query.filter(Supplier.id.in_(unique_ids)).all()
        found_ids = {s.id for s in suppliers}

        updated = 0
        for supplier in suppliers:
            if supplier.status != target_status:
                previous = supplier.to_dict()
                supplier.status = target_status
                action = "ACTIVATE" if target_status else "DEACTIVATE"
                SupplierService._log_audit(action, previous, supplier.to_dict())
                updated += 1

        if updated > 0:
            db.session.commit()

        not_found = len(unique_ids) - len(found_ids)
        return {"updated": updated, "not_found": not_found}
