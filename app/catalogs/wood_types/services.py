"""
Servicios de lógica de negocio para tipos de madera.
"""

from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.role import Role
from app.models.wood_type import WoodType

class WoodTypeService:
    """Servicio para operaciones de negocio relacionadas con tipos de madera."""

    @staticmethod
    def get_all() -> list[WoodType]:
        """
        Obtiene todos los tipos de madera activos.

        Returns:
            list[WoodType]: Lista de objetos WoodType activos
        """
        return WoodType.query.filter_by(active=True).all()

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo tipo de madera en el catálogo.

        Args:
            data: Diccionario con los datos del tipo de madera (name requerido)

        Returns:
            dict: Tipo de madera creado serializado

        Raises:
            ValidationError: Si el nombre está vacío o no se proporciona
            ConflictError: Si ya existe un tipo de madera con el mismo nombre
        """
        name = data.get("name")
        description = data.get("description")   

        if not name or not name.strip():
            raise ValidationError("El nombre del tipo de madera es requerido")

        name = name.strip()

        existing = WoodType.query.filter_by(name=name).first()
        if existing:
            raise ConflictError(f"Ya existe un tipo de madera con el nombre '{name}'")

        wood_type = WoodType(name=name, description=description)
        db.session.add(wood_type)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un tipo de madera con el nombre '{name}'")

        return wood_type.to_dict()

    @staticmethod
    def get_by_id(id_wood_type: int) -> WoodType:
        """
        Obtiene un tipo de madera por su ID.
        
        Args:
            id_wood_type: Identificador del tipo de madera.
            
        Returns:
            WoodType: Objeto del tipo de madera encontrado.
            
        Raises:
            NotFoundError: Si el tipo de madera no existe.
        """
        wood_type = WoodType.query.get(id_wood_type)
        if not wood_type:
            raise NotFoundError(f"No se encontró el tipo de madera con ID {id_wood_type}")
        return wood_type    

    @staticmethod
    def update(id_wood_type: int, data: dict) -> dict:
        """
        Actualiza un tipo de madera existente.

        Args:
            id_wood_type: ID del tipo de madera a actualizar
            data: Diccionario con los datos a actualizar (name, description)

        Returns:
            dict: Tipo de madera actualizado serializado

        Raises:
            ValidationError: Si el nombre está vacío o no se proporciona
            ConflictError: Si ya existe otro tipo de madera con el mismo nombre
            NotFoundError: Si no se encuentra el tipo de madera por ID
        """
        wood_type = WoodType.query.get(id_wood_type)
        if not wood_type or not wood_type.active:
            raise NotFoundError(f"No se encontró el tipo de madera con ID {id_wood_type}")

        name = data.get("name")
        description = data.get("description")

        if not name or not name.strip():
            raise ValidationError("El nombre del tipo de madera es requerido")

        name = name.strip()

        existing = WoodType.query.filter(WoodType.name == name, WoodType.id_wood_type != id_wood_type).first()
        if existing:
            raise ConflictError(f"Ya existe otro tipo de madera con el nombre '{name}'")

        wood_type.name = name
        wood_type.description = description

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe otro tipo de madera con el nombre '{name}'")

        return wood_type.to_dict()
    
    @staticmethod
    def delete(id_wood_type: int) -> None:
        """
        Elimina (desactiva) un tipo de madera por su ID.

        Args:
            id_wood_type: ID del tipo de madera a eliminar

        Raises:
            NotFoundError: Si no se encuentra el tipo de madera por ID
        """
        wood_type = WoodType.query.get(id_wood_type)
        if not wood_type or not wood_type.active:
            raise NotFoundError(f"No se encontró el tipo de madera con ID {id_wood_type}")

        wood_type.active = False
        db.session.commit()