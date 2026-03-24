"""
Servicios de lógica de negocio para colores.
"""

import re

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.color import Color


class ColorService:
    """Servicio para operaciones de negocio relacionadas con colores."""

    HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _log_audit(action: str, previous: dict | None, new: dict | None) -> None:
        """Registra un cambio en la tabla audit_log."""
        entry = AuditLog(
            table_name="colors",
            action=action,
            previous_data=previous,
            new_data=new,
        )
        db.session.add(entry)

    @staticmethod
    def _validate_hex(hex_code: str | None) -> str | None:
        """Valida y normaliza un código hexadecimal."""
        if not hex_code or not hex_code.strip():
            return None
        hex_code = hex_code.strip()
        if not ColorService.HEX_PATTERN.match(hex_code):
            raise ValidationError("El código hexadecimal debe tener el formato #RRGGBB")
        return hex_code.upper()

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
        Obtiene colores con búsqueda, filtro de estado y paginación.

        Returns:
            Pagination: Objeto de paginación de Flask-SQLAlchemy
        """
        query = Color.query

        # Filtro de estado
        if status_filter == "active":
            query = query.filter(Color.status.is_(True))
        elif status_filter == "inactive":
            query = query.filter(Color.status.is_(False))
        # 'all' o None → sin filtro

        # Búsqueda por nombre
        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(Color.name.ilike(term))

        query = query.order_by(Color.id.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_by_id(id_color: int) -> Color:
        """Obtiene un color por su ID."""
        color = db.session.get(Color, id_color)
        if not color:
            raise NotFoundError(f"No se encontró un color con ID {id_color}")
        return color

    # ------------------------------------------------------------------ #
    #  CREATE                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo color.

        Args:
            data: Diccionario con name (requerido), hex_code, description, status.

        Returns:
            dict: Color creado serializado.
        """
        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del color es requerido")
        name = name.strip()

        hex_code = ColorService._validate_hex(data.get("hex_code"))
        description = (data.get("description") or "").strip() or None
        status = data.get("status", True)
        if isinstance(status, str):
            status = status == "1"

        # Unicidad solo entre activos
        existing = Color.query.filter(
            func.lower(Color.name) == name.lower(),
            Color.status.is_(True),
        ).first()
        if existing:
            raise ConflictError(f"Ya existe un color activo con el nombre '{name}'")

        color = Color(
            name=name,
            hex_code=hex_code,
            description=description,
            status=status,
        )
        db.session.add(color)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un color con el nombre '{name}'")

        ColorService._log_audit("CREATE", None, color.to_dict())
        db.session.commit()

        return color.to_dict()

    # ------------------------------------------------------------------ #
    #  UPDATE                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def update(id_color: int, data: dict) -> dict:
        """
        Actualiza un color existente.

        Args:
            id_color: ID del color a actualizar.
            data: Diccionario con name, hex_code, description, status.
        """
        color = ColorService.get_by_id(id_color)
        previous = color.to_dict()

        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del color es requerido")
        name = name.strip()

        hex_code = ColorService._validate_hex(data.get("hex_code"))
        description = (data.get("description") or "").strip() or None
        status = data.get("status", color.status)
        if isinstance(status, str):
            status = status == "1"

        # Unicidad solo entre activos (excluyendo a sí mismo)
        existing = Color.query.filter(
            func.lower(Color.name) == name.lower(),
            Color.status.is_(True),
            Color.id != id_color,
        ).first()
        if existing:
            raise ConflictError(f"Ya existe otro color activo con el nombre '{name}'")

        color.name = name
        color.hex_code = hex_code
        color.description = description
        color.status = status

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe otro color con el nombre '{name}'")

        ColorService._log_audit("UPDATE", previous, color.to_dict())
        db.session.commit()

        return color.to_dict()

    # ------------------------------------------------------------------ #
    #  DELETE (soft-delete / toggle)                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def delete(id_color: int) -> None:
        """Desactiva un color (soft-delete)."""
        color = ColorService.get_by_id(id_color)
        previous = color.to_dict()
        color.status = not color.status
        ColorService._log_audit(
            "DEACTIVATE" if not color.status else "ACTIVATE",
            previous,
            color.to_dict(),
        )
        db.session.commit()

    @staticmethod
    def activate(id_color: int) -> None:
        """Activa un color."""
        color = ColorService.get_by_id(id_color)
        previous = color.to_dict()
        color.status = True
        ColorService._log_audit("ACTIVATE", previous, color.to_dict())
        db.session.commit()

    # ------------------------------------------------------------------ #
    #  BULK ACTIONS                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def bulk_deactivate(ids: list[int]) -> int:
        """Desactiva múltiples colores. Retorna la cantidad de desactivados."""
        colors = Color.query.filter(Color.id.in_(ids), Color.status.is_(True)).all()
        for color in colors:
            previous = color.to_dict()
            color.status = False
            ColorService._log_audit("DEACTIVATE", previous, color.to_dict())
        db.session.commit()
        return len(colors)

    @staticmethod
    def bulk_activate(ids: list[int]) -> int:
        """Activa múltiples colores. Retorna la cantidad de activados."""
        colors = Color.query.filter(Color.id.in_(ids), Color.status.is_(False)).all()
        for color in colors:
            previous = color.to_dict()
            color.status = True
            ColorService._log_audit("ACTIVATE", previous, color.to_dict())
        db.session.commit()
        return len(colors)
