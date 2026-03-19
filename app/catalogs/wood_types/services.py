"""
Servicios de lógica de negocio para tipos de madera.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from app.extensions import db
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.wood_type import WoodType


class WoodTypeService:
    """Servicio para operaciones de negocio relacionadas con tipos de madera."""

    @staticmethod
    def get_all(search_term: str = None, status_filter: str = "all") -> list[WoodType]:
        """
        Obtiene los tipos de madera, con opciones de filtrado.

        Args:
            search_term (str, optional): Término de búsqueda para el nombre o descripción.
            status_filter (str, optional): Estado para filtrar ('active', 'inactive', 'all').

        Returns:
            list[WoodType]: Lista de objetos WoodType
        """
        query = WoodType.query

        if search_term:
            search = f"%{search_term}%"
            query = query.filter(or_(WoodType.name.ilike(search), WoodType.description.ilike(search)))

        if status_filter == 'active':
            query = query.filter_by(status=True)
        elif status_filter == 'inactive':
            query = query.filter_by(status=False)
            
        return query.order_by(WoodType.id.desc()).all()

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

        wood_type = WoodType(name=name, description=description, status=data.get("status", True))
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
            raise NotFoundError(
                f"No se encontró el tipo de madera con ID {id_wood_type}"
            )
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
        if not wood_type:
            raise NotFoundError(
                f"No se encontró el tipo de madera con ID {id_wood_type}"
            )

        name = data.get("name")
        description = data.get("description")

        if not name or not name.strip():
            raise ValidationError("El nombre del tipo de madera es requerido")

        name = name.strip()

        existing = WoodType.query.filter(
            WoodType.name == name, WoodType.id != id_wood_type
        ).first()
        if existing:
            raise ConflictError(f"Ya existe otro tipo de madera con el nombre '{name}'")

        wood_type.name = name
        wood_type.description = description
        if "status" in data:
            wood_type.status = data["status"]

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe otro tipo de madera con el nombre '{name}'")

        return wood_type.to_dict()

    @staticmethod
    def toggle_status(id_wood_type: int) -> None:
        """
        Activa o inactiva un tipo de madera por su ID (toggle).

        Args:
            id_wood_type: ID del tipo de madera a ser alternado

        Raises:
            NotFoundError: Si no se encuentra el tipo de madera por ID
        """
        wood_type = WoodType.query.get(id_wood_type)
        if not wood_type:
            raise NotFoundError(
                f"No se encontró el tipo de madera con ID {id_wood_type}"
            )

        wood_type.status = not wood_type.status
        db.session.commit()

    @staticmethod
    def bulk_deactivate(ids: list[int]) -> int:
        """
        Desactiva múltiples tipos de madera por sus IDs.

        Args:
            ids: Lista de IDs de tipos de madera a desactivar

        Returns:
            int: Cantidad de registros desactivados
        """
        if not ids:
            return 0

        count = WoodType.query.filter(
            WoodType.id.in_(ids), WoodType.status == True
        ).update({WoodType.status: False}, synchronize_session="fetch")
        db.session.commit()
        return count

    @staticmethod
    def bulk_activate(ids: list[int]) -> int:
        """
        Activa múltiples tipos de madera por sus IDs.

        Args:
            ids: Lista de IDs de tipos de madera a activar

        Returns:
            int: Cantidad de registros activados
        """
        if not ids:
            return 0

        count = WoodType.query.filter(
            WoodType.id.in_(ids), WoodType.status == False  # noqa: E712
        ).update({WoodType.status: True}, synchronize_session="fetch")
        db.session.commit()
        return count
