"""
Servicios de lógica de negocio para unidades de medida.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from app.extensions import db
from app.models.unit_of_measure import UnitOfMeasure
from app.exceptions import ConflictError, ValidationError, NotFoundError


class UnitOfMeasureService:
    """Servicio para operaciones de negocio relacionadas con unidades de medida."""

    @staticmethod
    def get_all() -> list[UnitOfMeasure]:
        """
        Obtiene todas las unidades de medida activas.

        Returns:
            list[UnitOfMeasure]: Lista de objetos UnitOfMeasure activos
        """
        return UnitOfMeasure.query.filter_by(active=True).all()
    
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
        active = data.get("active", True) 
        if not name:
            raise ValidationError("El nombre de la unidad de medida es requerido")
        if not abbreviation:
            raise ValidationError("La abreviatura de la unidad de medida es requerida")
        existing = UnitOfMeasure.query.filter(func.lower(UnitOfMeasure.name) == func.lower(name)).first()
        if existing:
            raise ConflictError(f"Ya existe una unidad de medida con el nombre '{name}'")
        unit_of_measure = UnitOfMeasure(
            name=name,
            abbreviation=abbreviation,
            active=active
        )
        db.session.add(unit_of_measure)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("Ocurrió un error al crear la unidad de medida. Intente nuevamente.")
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
        
        name = data.get("name", "").strip() 
        abbreviation = data.get("abbreviation", "").strip() 
        

        if not name:
            raise ValidationError("El nombre de la unidad de medida es requerido")
        
        if not abbreviation:
            raise ValidationError("La abreviatura de la unidad de medida es requerida")

        existing = UnitOfMeasure.query.filter(
            func.lower(UnitOfMeasure.name) == func.lower(name),
            UnitOfMeasure.id_unit_of_measure != id_unit_of_measure  # Excluir la unidad actual del chequeo
        ).first()
        
        if existing:
            raise ConflictError(f"Ya existe una unidad de medida con el nombre '{name}'")

        unit_of_measure.name = name
        unit_of_measure.abbreviation = abbreviation
        

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("Ocurrió un error al actualizar la unidad de medida. Intente nuevamente.")

        return unit_of_measure.to_dict()
    
    @staticmethod
    def delete(id_unit_of_measure: int) -> None:
        """
        Elimina una unidad de medida del catálogo.

        Args:
            id_unit_of_measure (int): Identificador único de la unidad de medida a eliminar

        Raises:
            NotFoundError: Si no se encuentra la unidad de medida con el identificador dado
        """
        unit_of_measure = UnitOfMeasureService.get_by_id(id_unit_of_measure)
        
        unit_of_measure.active = False
        unit_of_measure.deleted_at = func.current_timestamp()

        db.session.commit()