"""
Servicios de lógica de negocio para colores.
"""

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, ValidationError, NotFoundError
from app.extensions import db
from app.models.color import Color


class ColorService:
    """Servicio para operaciones de negocio relacionadas con colores."""

    @staticmethod
    def get_all() -> list[Color]:
        """
        Obtiene todos los colores activos.

        Returns:
            list[Color]: Lista de objetos Color activos
        """
        return Color.query.filter_by(active=True).all()

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo color en el catálogo.

        Args:
            data: Diccionario con los datos del color (name requerido)

        Returns:
            dict: Color creado serializado

        Raises:
            ValidationError: Si el nombre está vacío o no se proporciona
            ConflictError: Si ya existe un color con el mismo nombre
        """
        name = data.get("name")

        if not name or not name.strip():
            raise ValidationError("El nombre del color es requerido")

        name = name.strip()

        existing = Color.query.filter(func.lower(Color.name) == name.lower()).first()
        if existing:
            raise ConflictError(f"Ya existe un color con el nombre '{name}'")

        color = Color(name=name)
        db.session.add(color)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un color con el nombre '{name}'")

        return color.to_dict()

    @staticmethod
    def get_by_id(id_color: int) -> Color:
        """
        Obtiene un color por su ID.

        Args:
            id_color: Identificador del color a obtener

        Returns:
            Color: Objeto Color correspondiente al ID

        Raises:
            NotFoundError: Si no se encuentra un color con el ID proporcionado
        """
        color = Color.query.get(id_color)

        if not color:
            raise NotFoundError(f"No se encontró un color con ID {id_color}")
        return color

    @staticmethod
    def update(id_color: int, data: dict) -> dict:
        """
        Actualiza un color existente.

        Args:
            id_color: Identificador del color a actualizar
            data: Diccionario con los datos actualizados del color (name requerido)

        Returns:
            dict: Color actualizado serializado

        Raises:
            NotFoundError: Si no se encuentra un color con el ID proporcionado
            ValidationError: Si el nombre está vacío o no se proporciona
            ConflictError: Si ya existe otro color con el mismo nombre
        """
        color = ColorService.get_by_id(id_color)

        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del color es requerido")

        name = name.strip()

        existing = (
                db.session.query(Color.id_color)
                .filter(func.lower(Color.name) == name.lower(), Color.id_color != id_color)
                .first()
                is not None
        )

        if existing:
            raise ConflictError(f"Ya existe otro color con el nombre '{name}'")

        color.name = name

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe otro color con el nombre '{name}'")

        return color.to_dict()

    @staticmethod
    def delete(id_color: int) -> None:
        """
        Elimina un color con el ID.
        Args:
            id_color: Identificador del color a eliminar

        Raises:
            NotFoundError: Si no se encuentra un color con el ID

        """
        color = ColorService.get_by_id(id_color)

        color.active = False
        color.deleted_at = func.current_timestamp()

        db.session.commit()
