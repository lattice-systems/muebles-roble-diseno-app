import re

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from flask_security.utils import hash_password

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.role import Role
from app.models.user import User


class UserService:
	"""Servicio para operaciones de negocio relacionadas con usuarios."""

	@staticmethod
	def get_all(
		search_term: str | None = None,
		status_filter: str | None = None,
		page: int = 1,
		per_page: int = 10,
	):
		"""
		Obtiene usuarios con búsqueda, filtro de estado y paginación.

		Returns:
			Pagination: Objeto de paginación de Flask-SQLAlchemy
		"""
		query = User.query.options(joinedload(User.role))

		if status_filter == "active":
			query = query.filter(User.status.is_(True))
		elif status_filter == "inactive":
			query = query.filter(User.status.is_(False))

		if search_term and search_term.strip():
			term = f"%{search_term.strip()}%"
			query = query.filter(
				or_(
					User.full_name.ilike(term),
					User.email.ilike(term),
				)
			)

		query = query.order_by(User.id.desc())
		return query.paginate(page=page, per_page=per_page, error_out=False)

	@staticmethod
	def get_by_id(id_user: int) -> User:
		"""Obtiene un usuario por su ID."""
		user = db.session.get(User, id_user)
		if not user:
			raise NotFoundError(f"No se encontró un usuario con ID {id_user}")
		return user

	@staticmethod
	def get_role_choices() -> list[tuple[int, str]]:
		"""Retorna roles activos para usuarios internos (excluye Cliente)."""
		roles = (
			Role.query.filter(
				Role.status.is_(True),
				func.lower(Role.name) != "cliente",
			)
			.order_by(Role.name.asc())
			.all()
		)
		return [(role.id, role.name) for role in roles]

	@staticmethod
	def create(data: dict) -> User:
		"""Crea un nuevo usuario con validaciones básicas de negocio."""
		full_name = (data.get("full_name") or "").strip()
		email = (data.get("email") or "").strip().lower()
		password = data.get("password") or ""
		role_id = data.get("role_id")
		status = data.get("status", True)

		if not full_name:
			raise ValidationError("El nombre completo es requerido")
		if len(full_name) > 150:
			raise ValidationError("El nombre no puede exceder 150 caracteres")
		if not email:
			raise ValidationError("El correo electrónico es requerido")
		if len(email) > 120:
			raise ValidationError("El correo no puede exceder 120 caracteres")
		if not password:
			raise ValidationError("La contraseña es requerida")
		if len(password) < 8:
			raise ValidationError("La contraseña debe tener al menos 8 caracteres")
		if not re.search(r"[A-Z]", password):
			raise ValidationError("La contraseña debe incluir al menos una mayúscula")
		if not re.search(r"[a-z]", password):
			raise ValidationError("La contraseña debe incluir al menos una minúscula")
		if not re.search(r"\d", password):
			raise ValidationError("La contraseña debe incluir al menos un número")
		if not re.search(r"[^A-Za-z0-9]", password):
			raise ValidationError(
				"La contraseña debe incluir al menos un carácter especial"
			)
		if role_id is None:
			raise ValidationError("Debe seleccionar un rol")

		role = db.session.get(Role, role_id)
		if not role:
			raise ValidationError("El rol seleccionado no existe")
		if not role.status:
			raise ValidationError("El rol seleccionado está desactivado")

		existing = User.query.filter(User.email.ilike(email)).first()
		if existing:
			raise ConflictError(f"Ya existe un usuario con el correo '{email}'")

		if isinstance(status, str):
			status = status.lower() in {"1", "true", "on", "yes"}

		user = User(
			full_name=full_name,
			email=email,
			password_hash=hash_password(password),
			role_id=role_id,
			status=bool(status),
		)

		db.session.add(user)
		try:
			db.session.commit()
		except IntegrityError:
			db.session.rollback()
			raise ConflictError(f"Ya existe un usuario con el correo '{email}'")

		return user

	@staticmethod
	def toggle_status(id_user: int) -> bool:
		"""Alterna el estado (activo/inactivo) de un usuario y retorna el estado final."""
		user = UserService.get_by_id(id_user)
		user.status = not user.status
		db.session.commit()
		return user.status
