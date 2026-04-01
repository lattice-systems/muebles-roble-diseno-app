"""
Servicios de lógica de negocio para tipo de mueble.
"""

import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from app.extensions import db
from app.models.furniture_type import FurnitureType
from app.exceptions import ConflictError, ValidationError, NotFoundError


class FurnitureTypeService:
    """Servicio para operaciones de negocio relacionadas con tipo de mueble."""

    @staticmethod
    def _slugify(value: str) -> str:
        text = value.lower().strip()
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s-]+", "-", text)
        return text.strip("-")

    @staticmethod
    def _build_unique_slug(base_slug: str, exclude_id: int | None = None) -> str:
        slug = base_slug or "categoria"
        counter = 2

        while True:
            query = FurnitureType.query.filter(FurnitureType.slug == slug)
            if exclude_id is not None:
                query = query.filter(FurnitureType.id != exclude_id)

            if query.first() is None:
                return slug

            slug = f"{base_slug}-{counter}"
            counter += 1

    @staticmethod
    def get_all(
        search_term: str = None,
        status_filter: str = "all",
        page: int = 1,
        per_page: int = 10,
    ):
        """
        Obtiene los tipos de mueble paginados, con opciones de filtrado.
        """
        query = FurnitureType.query

        if search_term:
            search = f"%{search_term}%"
            query = query.filter(or_(FurnitureType.title.ilike(search)))

        if status_filter == "active":
            query = query.filter_by(status=True)
        elif status_filter == "inactive":
            query = query.filter_by(status=False)

        return query.order_by(FurnitureType.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo tipo de mueble en el catálogo.
        """
        title = (data.get("title") or "").strip()

        if not title:
            raise ValidationError("El titulo del tipo de mueble es requerido")

        existing = FurnitureType.query.filter_by(title=title).first()
        if existing:
            raise ConflictError(f"Ya existe un tipo de mueble con el titulo '{title}'")

        base_slug = FurnitureTypeService._slugify(title)
        slug = FurnitureTypeService._build_unique_slug(base_slug)

        furniture_type = FurnitureType(
            title=title,
            slug=slug,
            status=data.get("status", True),
        )
        db.session.add(furniture_type)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un tipo de mueble con el titulo '{title}'")

        return furniture_type.to_dict()

    @staticmethod
    def get_by_id(id_furniture_type: int) -> FurnitureType:
        """
        Obtiene un tipo de mueble por su ID.
        """
        furniture_type = FurnitureType.query.get(id_furniture_type)
        if not furniture_type:
            raise NotFoundError(
                f"No se encontró el tipo de mueble con ID {id_furniture_type}"
            )
        return furniture_type

    @staticmethod
    def update(id_furniture_type: int, data: dict) -> dict:
        """
        Actualiza un tipo de mueble existente con validaciones de negocio.
        """
        furniture_type = FurnitureTypeService.get_by_id(id_furniture_type)

        title = (data.get("title") or "").strip()
        if not title:
            raise ValidationError("El titulo del mueble es requerido")

        existing = FurnitureType.query.filter(
            FurnitureType.title == title,
            FurnitureType.id != id_furniture_type,
        ).first()
        if existing:
            raise ConflictError(f"Ya existe un tipo de mueble con el titulo '{title}'")

        base_slug = FurnitureTypeService._slugify(title)
        slug = FurnitureTypeService._build_unique_slug(
            base_slug,
            exclude_id=id_furniture_type,
        )

        furniture_type.title = title
        furniture_type.slug = slug
        if "status" in data:
            furniture_type.status = data["status"]

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(
                f"Error de integridad al actualizar el tipo de mueble '{title}'"
            )

        return furniture_type.to_dict()

    @staticmethod
    def toggle_status(id_furniture_type: int) -> None:
        """
        Activa o inactiva un tipo de mueble por su ID (toggle).
        """
        furniture_type = FurnitureTypeService.get_by_id(id_furniture_type)
        furniture_type.status = not furniture_type.status
        db.session.commit()

    @staticmethod
    def bulk_deactivate(ids: list[int]) -> int:
        """
        Desactiva múltiples tipos de mueble por sus IDs.
        """
        if not ids:
            return 0

        count = FurnitureType.query.filter(
            FurnitureType.id.in_(ids), FurnitureType.status == True  # noqa: E712
        ).update({FurnitureType.status: False}, synchronize_session="fetch")
        db.session.commit()
        return count

    @staticmethod
    def bulk_activate(ids: list[int]) -> int:
        """
        Activa múltiples tipos de mueble por sus IDs.
        """
        if not ids:
            return 0

        count = FurnitureType.query.filter(
            FurnitureType.id.in_(ids), FurnitureType.status == False  # noqa: E712
        ).update({FurnitureType.status: True}, synchronize_session="fetch")
        db.session.commit()
        return count
