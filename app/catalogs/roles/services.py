"""
Servicios de lógica de negocio para roles.
"""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.role import Role
from app.exceptions import ConflictError, ValidationError, NotFoundError


class RoleService:
    """Servicio para operaciones de negocio relacionadas con roles."""

    @staticmethod
    def get_all() -> list[Role]:
        """
        Obtiene todos los roles activos.

        Returns:
            list[Role]: Lista de objetos Role activos
        """
        return Role.query.filter_by(status=True).all()

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo rol en el catálogo.

        Args:
            data: Diccionario con los datos del rol (name requerido)

        Returns:
            dict: Rol creado serializado

        Raises:
            ValidationError: Si el nombre está vacío o no se proporciona
            ConflictError: Si ya existe un rol con el mismo nombre
        """
        name = data.get("name")

        if not name or not name.strip():
            raise ValidationError("El nombre del rol es requerido")

        name = name.strip()

        existing = Role.query.filter_by(name=name).first()
        if existing:
            raise ConflictError(f"Ya existe un rol con el nombre '{name}'")

        role = Role(name=name)
        db.session.add(role)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Ya existe un rol con el nombre '{name}'")

        return role.to_dict()

    @staticmethod
    def get_by_id(id_role: int) -> Role:
        """
        Obtiene un rol por su ID.

        Args:
            id_role: Identificador del rol.

        Returns:
            Role: Objeto del rol encontrado.

        Raises:
            NotFoundError: Si el rol no existe.
        """
        role = Role.query.get(id_role)
        if not role:
            raise NotFoundError(f"No se encontró el rol con ID {id_role}")
        return role

    @staticmethod
    def update(id_role: int, data: dict) -> dict:
        """
        Actualiza un rol existente con validaciones de negocio.

        Args:
            id_role: ID del rol a actualizar.
            data: Diccionario con los datos del rol (name requerido).

        Returns:
            dict: Rol actualizado serializado.

        Raises:
            NotFoundError: Si el rol no existe.
            ValidationError: Si el nombre está vacío.
            ConflictError: Si ya existe otro rol con el mismo nombre.
        """
        role = RoleService.get_by_id(id_role)

        name = data.get("name")
        if not name or not name.strip():
            raise ValidationError("El nombre del rol es requerido")

        name = name.strip()

        # Verificar si existe OTRO rol diferente que ya tenga este nombre
        existing = Role.query.filter(Role.name == name, Role.id != id_role).first()
        if existing:
            raise ConflictError(f"Ya existe un rol con el nombre '{name}'")

        role.name = name

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError(f"Error de integridad al actualizar el rol '{name}'")

        return role.to_dict()

    @staticmethod
    def delete(id_role: int) -> None:
        """
        Realiza una eliminación lógica (Soft Delete) de un rol.

        Marca el rol como inactivo y establece la fecha de eliminación.
        No elimina el registro de la base de datos.

        Args:
            id_role: Identificador del rol a eliminar.

        Raises:
            NotFoundError: Si el rol no existe.
        """
        # Reutilizamos el método get_by_id para aprovechar la validación de existencia
        role = RoleService.get_by_id(id_role)

        # Aplicamos el Soft Delete
        role.status = False

        db.session.commit()
