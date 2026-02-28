"""
Servicios de lógica de negocio para tipo de mueble.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from app.extensions import db
from app.models.furniture_type import FurnitureType
from app.exceptions import ConflictError, ValidationError, NotFoundError


class FurnitureTypeService:
    """Servicio para operaciones de negocio relacionadas con tipo de mueble."""

    @staticmethod
    def get_all() -> list[FurnitureType]:
        """
        Obtiene todos los tipo de mueble activos.

        Returns:
            list[FurnitureType]: Lista de objetos FurnitureType activos
        """
        return FurnitureType.query.filter_by(active=True).all()

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo tipo de mueble en el catálogo.

        Args:
            data: Diccionario con los datos del tipo de mueble (name requerido)

        Returns:
            dict: Tipo de mueble creado serializado

        Raises:
            ValidationError: Si el nombre está vacío o no se proporciona
            ConflictError: Si ya existe un tipo de mueble con el mismo nombre
        """
        name = data.get("name")

        if not name or not name.strip():
            raise ValidationError("El nombre del tipo de mueble es requerido")

        name = name.strip()

        existing = FurnitureType.query.filter_by(name=name).first()
        if existing:
            raise ConflictError(f"Ya existe un tipo de mueble con el nombre '{name}'")

        furniture_type = FurnitureType(name=name)
        db.session.add(furniture_type)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un tipo de mueble con el nombre '{name}'")

        return furniture_type.to_dict()

    @staticmethod
    def get_by_id(id_furniture_type: int) -> FurnitureType:
        """
        Obtiene un tipo de mueble por su ID.
        
        Args:
            id_, NotFoundError: Identificador del tipo de mueble.
            
        Returns:
            FurnitureType: Objeto del tipo de mueble encontrado.
            
        Raises:
            NotFoundError: Si el tipo de mueble no existe.
        """
        furniture_type = FurnitureType.query.get(id_furniture_type)
        if not furniture_type:
            raise NotFoundError(f"No se encontró el tipo de mueble con ID {id_furniture_type}")
        return furniture_type

    @staticmethod
    def update(id_furniture_type: int, data: dict) -> dict:
        """
        Actualiza un tipo de mueble existente con validaciones de negocio.

        Args:
            id_, NotFoundError: ID del tipo de mueble a actualizar.
            data: Diccionario con los datos del tipo de mueble (name requerido).

        Returns:
            dict: FurnitureType actualizado serializado.

        Raises:
            NotFoundError: Si el tipo de mueble no existe.
            ValidationError: Si el nombre está vacío.
            ConflictError: Si ya existe otro tipo de mueble con el mismo nombre.
        """
        furniture_type = FurnitureTypeService.get_by_id(id_furniture_type)

        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del furniture_type es requerido")

        name = name.strip()

        # Verificar si existe OTRO tipo de mueble diferente que ya tenga este nombre
        existing = FurnitureType.query.filter(FurnitureType.name == name, FurnitureType.id_furniture_type != id_furniture_type).first()
        if existing:
            raise ConflictError(f"Ya existe un tipo de mueble con el nombre '{name}'")

        furniture_type.name = name

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Error de integridad al actualizar el tipo de mueble '{name}'")

        return furniture_type.to_dict()

    @staticmethod
    def delete(id_furniture_type: int) -> None:
        """
        Realiza una eliminación lógica (Soft Delete) de un tipo de mueble.

        Marca el tipo de mueble como inactivo y establece la fecha de eliminación.
        No elimina el registro de la base de datos.

        Args:
            id_furniture_type: Identificador del tipo de mueble a eliminar.

        Raises:
            NotFoundError: Si el tipo de mueble no existe.
        """
        # Reutilizamos el método get_by_id para aprovechar la validación de existencia
        furniture_type = FurnitureTypeService.get_by_id(id_furniture_type)

        # Aplicamos el Soft Delete
        furniture_type.active = False
        furniture_type.deleted_at = func.current_timestamp()

        db.session.commit()
