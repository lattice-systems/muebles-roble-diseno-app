"""
Servicios de lógica de negocio para unidades de medida.
"""

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.unit_of_measure import UnitOfMeasure
from app.exceptions import ConflictError, ValidationError, NotFoundError
from app.shared.audit_logging import log_application_audit


class UnitOfMeasureService:
    """Servicio para operaciones de negocio relacionadas con unidades de medida."""

    @staticmethod
    def get_all(
        search_term: str = "",
        status_filter: str = "all",
        page: int = 1,
        per_page: int = 10,
    ):
        """
        Obtiene las unidades de medida con filtros de búsqueda y paginación.
        """
        query = UnitOfMeasure.query

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                db.or_(
                    UnitOfMeasure.name.ilike(search_pattern),
                    UnitOfMeasure.abbreviation.ilike(search_pattern),
                )
            )

        if status_filter == "active":
            query = query.filter(UnitOfMeasure.status)
        elif status_filter == "inactive":
            query = query.filter(not UnitOfMeasure.status)

        return query.order_by(UnitOfMeasure.id_unit_of_measure.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea una nueva unidad de medida.

        Args:
            data (dict): Diccionario con los datos de la unidad de medida a crear

        Returns:
            dict: La unidad de medida creada

        Raises:
            ValidationError: Si los datos proporcionados no son válidos
            ConflictError: Si ya existe una unidad de medida con el mismo nombre
        """
        name = data.get("name", "").strip()
        abbreviation = data.get("abbreviation", "").strip()
        unit_type = data.get("type", "").strip()
        active = data.get("active", True)

        if not name:
            raise ValidationError("El nombre de la unidad de medida es requerido")
        if not abbreviation:
            raise ValidationError("La abreviatura de la unidad de medida es requerida")
        if unit_type not in ["longitud", "peso", "volumen", "unidad"]:
            raise ValidationError(
                "El tipo de unidad debe ser longitud, peso, volumen o unidad"
            )

        # Validamos que no exista otra unidad con la misma abreviatura que esté activa
        existing = UnitOfMeasure.query.filter(
            func.lower(UnitOfMeasure.abbreviation) == func.lower(abbreviation),
            UnitOfMeasure.status,
        ).first()
        if existing:
            raise ConflictError(
                f"Ya existe una unidad de medida activa con la abreviatura '{abbreviation}'"
            )

        unit_of_measure = UnitOfMeasure(
            name=name, abbreviation=abbreviation, type=unit_type, status=active
        )
        db.session.add(unit_of_measure)
        try:
            db.session.commit()

            # Registrar auditoria de aplicacion (fallback fuera de MySQL)
            log_application_audit(
                table_name="units",
                action="CREATE",
                new_data=unit_of_measure.to_dict(),
            )
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            raise ConflictError(
                "Ocurrió un error al crear la unidad de medida. Asegúrese de que no viole restricciones de la base de datos."
            )
        return unit_of_measure.to_dict()

    @staticmethod
    def get_by_id(id_unit_of_measure: int) -> UnitOfMeasure:
        """
        Obtiene una unidad de medida por su identificador único.

        Args:
            id_unit_of_measure (int): Identificador único de la unidad de medida

        Returns:
            UnitOfMeasure: La unidad de medida encontrada

        Raises:
            NotFoundError: Si no se encuentra la unidad de medida con el identificador dado
        """
        unit_of_measure = UnitOfMeasure.query.get(id_unit_of_measure)
        if not unit_of_measure:
            raise NotFoundError("Unidad de medida no encontrada")
        return unit_of_measure

    @staticmethod
    def get_by_ids(ids: list[int]) -> list[UnitOfMeasure]:
        """Obtiene multiples unidades de medida por IDs."""
        if not ids:
            return []
        return UnitOfMeasure.query.filter(
            UnitOfMeasure.id_unit_of_measure.in_(ids)
        ).all()

    @staticmethod
    def update(id_unit_of_measure: int, data: dict) -> dict:
        """
        Actualiza una unidad de medida existente.

        Args:
            id_unit_of_measure (int): Identificador único de la unidad de medida a actualizar
            data (dict): Diccionario con los nuevos datos de la unidad de medida

        Returns:
            dict: La unidad de medida actualizada

        Raises:
            ValidationError: Si los datos proporcionados no son válidos
            ConflictError: Si ya existe una unidad de medida con el mismo nombre
            NotFoundError: Si no se encuentra la unidad de medida con el identificador dado
        """
        unit_of_measure = UnitOfMeasureService.get_by_id(id_unit_of_measure)
        previous_data = unit_of_measure.to_dict()

        name = data.get("name", "").strip()
        abbreviation = data.get("abbreviation", "").strip()
        unit_type = data.get("type", "").strip()
        active = data.get("active", unit_of_measure.status)

        if not name:
            raise ValidationError("El nombre de la unidad de medida es requerido")

        if not abbreviation:
            raise ValidationError("La abreviatura de la unidad de medida es requerida")

        if unit_type not in ["longitud", "peso", "volumen", "unidad"]:
            raise ValidationError(
                "El tipo de unidad debe ser longitud, peso, volumen o unidad"
            )

        existing = UnitOfMeasure.query.filter(
            func.lower(UnitOfMeasure.abbreviation) == func.lower(abbreviation),
            UnitOfMeasure.status,
            UnitOfMeasure.id != id_unit_of_measure,
        ).first()

        if existing:
            raise ConflictError(
                f"Ya existe una unidad de medida activa con la abreviatura '{abbreviation}'"
            )

        unit_of_measure.name = name
        unit_of_measure.abbreviation = abbreviation
        unit_of_measure.type = unit_type
        unit_of_measure.status = active

        try:
            db.session.commit()

            # Registrar auditoria de aplicacion (fallback fuera de MySQL)
            log_application_audit(
                table_name="units",
                action="UPDATE",
                previous_data=previous_data,
                new_data=unit_of_measure.to_dict(),
            )
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            raise ConflictError(
                "Ocurrió un error al actualizar la unidad de medida. Asegúrese de que no viole restricciones de la base de datos."
            )

        return unit_of_measure.to_dict()

    @staticmethod
    def toggle_status(id_unit_of_measure: int) -> None:
        """
        Alterna el estado de una unidad de medida.

        Args:
            id_unit_of_measure (int): Identificador único de la unidad de medida a alterar

        Raises:
            NotFoundError: Si no se encuentra la unidad de medida con el identificador dado
        """
        unit_of_measure = UnitOfMeasureService.get_by_id(id_unit_of_measure)
        previous_data = unit_of_measure.to_dict()

        unit_of_measure.status = not unit_of_measure.status

        db.session.commit()

        # Registrar auditoria de aplicacion (fallback fuera de MySQL)
        log_application_audit(
            table_name="units",
            action="TOGGLE_STATUS",
            previous_data=previous_data,
            new_data=unit_of_measure.to_dict(),
        )
        db.session.commit()

    @staticmethod
    def bulk_toggle_status(ids: list[int], target_status: bool) -> None:
        """
        Cambia el estado de múltiples unidades de medida y registra la auditoría.
        """
        units = UnitOfMeasure.query.filter(
            UnitOfMeasure.id_unit_of_measure.in_(ids)
        ).all()
        for unit in units:
            previous_data = unit.to_dict()
            unit.status = target_status
            log_application_audit(
                table_name="units",
                action="BULK_UPDATE_STATUS",
                previous_data=previous_data,
                new_data=unit.to_dict(),
            )
        db.session.commit()
