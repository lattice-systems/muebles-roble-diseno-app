from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.exceptions import NotFoundError
from app.extensions import db
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
	def toggle_status(id_user: int) -> bool:
		"""Alterna el estado (activo/inactivo) de un usuario y retorna el estado final."""
		user = UserService.get_by_id(id_user)
		user.status = not user.status
		db.session.commit()
		return user.status
