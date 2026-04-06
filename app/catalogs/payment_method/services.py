"""
Servicios de lógica de negocio para métodos de pago.
"""

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.payment_method import PaymentMethod
from app.shared.audit_logging import log_application_audit


class PaymentMethodService:
    """Servicio para operaciones de negocio relacionadas con métodos de pago."""

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _log_audit(action: str, previous: dict | None, new: dict | None) -> None:
        """Registra auditoria de aplicacion (fallback fuera de MySQL)."""
        log_application_audit(
            table_name="payment_methods",
            action=action,
            previous_data=previous,
            new_data=new,
        )

    # ------------------------------------------------------------------ #
    #  READ                                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_all(
        search_term: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """
        Obtiene métodos de pago con búsqueda, filtro de estado y paginación.

        Returns:
            Pagination: Objeto de paginación de Flask-SQLAlchemy
        """
        query = PaymentMethod.query

        # Filtro de estado
        if status_filter == "active":
            query = query.filter(PaymentMethod.status.is_(True))
        elif status_filter == "inactive":
            query = query.filter(PaymentMethod.status.is_(False))
        # 'all' o None → sin filtro

        # Búsqueda por nombre o tipo
        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(
                (PaymentMethod.name.ilike(term)) | (PaymentMethod.type.ilike(term))
            )

        query = query.order_by(PaymentMethod.id.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_by_id(id_payment_method: int) -> PaymentMethod:
        """Obtiene un método de pago por su ID."""
        payment_method = db.session.get(PaymentMethod, id_payment_method)
        if not payment_method:
            raise NotFoundError(
                f"No se encontró un método de pago con ID {id_payment_method}"
            )
        return payment_method

    @staticmethod
    def get_by_ids(ids: list[int]) -> list[PaymentMethod]:
        """Obtiene multiples métodos de pago por IDs."""
        if not ids:
            return []
        return PaymentMethod.query.filter(PaymentMethod.id.in_(ids)).all()

    # ------------------------------------------------------------------ #
    #  CREATE                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo método de pago.

        Args:
            data: Diccionario con name, type, description, status, available_pos, available_ecommerce.

        Returns:
            dict: Método de pago creado serializado.
        """
        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del método de pago es requerido")
        name = name.strip()

        pm_type = data.get("type")
        if not pm_type or not pm_type.strip():
            raise ValidationError("El tipo de método de pago es requerido")
        pm_type = pm_type.strip().lower()

        description = (data.get("description") or "").strip() or None

        status = data.get("status", True)
        if isinstance(status, str):
            status = status == "1"

        available_pos = data.get("available_pos", True)
        if isinstance(available_pos, str):
            available_pos = available_pos.lower() == "true" or available_pos == "1"

        available_ecommerce = data.get("available_ecommerce", True)
        if isinstance(available_ecommerce, str):
            available_ecommerce = (
                available_ecommerce.lower() == "true" or available_ecommerce == "1"
            )

        # Unicidad solo entre activos
        existing = PaymentMethod.query.filter(
            func.lower(PaymentMethod.name) == name.lower(),
            PaymentMethod.status.is_(True),
        ).first()
        if existing:
            raise ConflictError(
                f"Ya existe un método de pago activo con el nombre '{name}'"
            )

        payment_method = PaymentMethod(
            name=name,
            type=pm_type,
            description=description,
            status=status,
            available_pos=available_pos,
            available_ecommerce=available_ecommerce,
        )
        db.session.add(payment_method)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un método de pago con el nombre '{name}'")

        PaymentMethodService._log_audit("CREATE", None, payment_method.to_dict())
        db.session.commit()

        return payment_method.to_dict()

    # ------------------------------------------------------------------ #
    #  UPDATE                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def update(id_payment_method: int, data: dict) -> dict:
        """
        Actualiza un método de pago existente.

        Args:
            id_payment_method: ID del método a actualizar.
            data: Diccionario con name, type, description, status, available_pos, available_ecommerce.
        """
        payment_method = PaymentMethodService.get_by_id(id_payment_method)
        previous = payment_method.to_dict()

        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del método de pago es requerido")
        name = name.strip()

        pm_type = data.get("type")
        if not pm_type or not pm_type.strip():
            raise ValidationError("El tipo de método de pago es requerido")
        pm_type = pm_type.strip().lower()

        description = (data.get("description") or "").strip() or None

        status = data.get("status", payment_method.status)
        if isinstance(status, str):
            status = status == "1"

        available_pos = data.get("available_pos", payment_method.available_pos)
        if isinstance(available_pos, str):
            available_pos = available_pos.lower() == "true" or available_pos == "1"

        available_ecommerce = data.get(
            "available_ecommerce", payment_method.available_ecommerce
        )
        if isinstance(available_ecommerce, str):
            available_ecommerce = (
                available_ecommerce.lower() == "true" or available_ecommerce == "1"
            )

        # Unicidad solo entre activos (excluyendo a sí mismo)
        existing = PaymentMethod.query.filter(
            func.lower(PaymentMethod.name) == name.lower(),
            PaymentMethod.status.is_(True),
            PaymentMethod.id != id_payment_method,
        ).first()
        if existing:
            raise ConflictError(
                f"Ya existe otro método de pago activo con el nombre '{name}'"
            )

        payment_method.name = name
        payment_method.type = pm_type
        payment_method.description = description
        payment_method.status = status
        payment_method.available_pos = available_pos
        payment_method.available_ecommerce = available_ecommerce

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe otro método de pago con el nombre '{name}'")

        PaymentMethodService._log_audit("UPDATE", previous, payment_method.to_dict())
        db.session.commit()

        return payment_method.to_dict()

    # ------------------------------------------------------------------ #
    #  DELETE (soft-delete / toggle)                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def delete(id_payment_method: int) -> None:
        """Desactiva un método de pago (soft-delete). Toggle status."""
        payment_method = PaymentMethodService.get_by_id(id_payment_method)
        previous = payment_method.to_dict()
        payment_method.status = not payment_method.status
        PaymentMethodService._log_audit(
            "DEACTIVATE" if not payment_method.status else "ACTIVATE",
            previous,
            payment_method.to_dict(),
        )
        db.session.commit()

    @staticmethod
    def activate(id_payment_method: int) -> None:
        """Activa un método de pago."""
        payment_method = PaymentMethodService.get_by_id(id_payment_method)
        previous = payment_method.to_dict()
        payment_method.status = True
        PaymentMethodService._log_audit("ACTIVATE", previous, payment_method.to_dict())
        db.session.commit()

    # ------------------------------------------------------------------ #
    #  BULK ACTIONS                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def bulk_deactivate(ids: list[int]) -> int:
        """Desactiva múltiples métodos de pago. Retorna la cantidad de desactivados."""
        methods = PaymentMethod.query.filter(
            PaymentMethod.id.in_(ids), PaymentMethod.status.is_(True)
        ).all()
        for method in methods:
            previous = method.to_dict()
            method.status = False
            PaymentMethodService._log_audit("DEACTIVATE", previous, method.to_dict())
        db.session.commit()
        return len(methods)

    @staticmethod
    def bulk_activate(ids: list[int]) -> int:
        """Activa múltiples métodos de pago. Retorna la cantidad de activados."""
        methods = PaymentMethod.query.filter(
            PaymentMethod.id.in_(ids), PaymentMethod.status.is_(False)
        ).all()
        for method in methods:
            previous = method.to_dict()
            method.status = True
            PaymentMethodService._log_audit("ACTIVATE", previous, method.to_dict())
        db.session.commit()
        return len(methods)
