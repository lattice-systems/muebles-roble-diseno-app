"""Servicios para consulta del modulo de auditoria."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import joinedload

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Servicio para consultas y filtros de auditoria."""

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        """Convierte una fecha YYYY-MM-DD a date de forma tolerante."""
        if not value:
            return None

        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def get_by_id(audit_id: int) -> AuditLog:
        """Retorna un registro de auditoria por id."""
        item = (
            AuditLog.query.options(joinedload(AuditLog.user))
            .filter(AuditLog.id == audit_id)
            .first()
        )

        if not item:
            raise NotFoundError(
                f"No se encontro un evento de auditoria con ID {audit_id}"
            )

        return item

    @staticmethod
    def get_filter_options() -> dict[str, list]:
        """Retorna listas para filtros dinamicos de la pantalla de auditoria."""
        table_names = [
            row[0]
            for row in db.session.query(AuditLog.table_name)
            .distinct()
            .order_by(AuditLog.table_name.asc())
            .all()
            if row[0]
        ]

        actions = [
            row[0]
            for row in db.session.query(AuditLog.action)
            .distinct()
            .order_by(AuditLog.action.asc())
            .all()
            if row[0]
        ]

        sources = [
            row[0]
            for row in db.session.query(AuditLog.source)
            .distinct()
            .order_by(AuditLog.source.asc())
            .all()
            if row[0]
        ]

        users = (
            db.session.query(User.id, User.full_name)
            .join(AuditLog, AuditLog.user_id == User.id)
            .distinct()
            .order_by(User.full_name.asc())
            .all()
        )

        return {
            "table_names": table_names,
            "actions": actions,
            "sources": sources,
            "users": users,
        }

    @staticmethod
    def get_logs(
        *,
        search_term: str | None = None,
        table_name: str | None = None,
        action: str | None = None,
        source: str | None = None,
        user_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        """Consulta paginada de auditoria con filtros combinables."""
        query = AuditLog.query.options(joinedload(AuditLog.user))

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    AuditLog.table_name.ilike(term),
                    AuditLog.action.ilike(term),
                    AuditLog.source.ilike(term),
                    cast(AuditLog.record_id, String).ilike(term),
                )
            )

        if table_name:
            query = query.filter(AuditLog.table_name == table_name)

        if action:
            query = query.filter(AuditLog.action == action)

        if source:
            query = query.filter(AuditLog.source == source)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if date_from:
            query = query.filter(
                AuditLog.timestamp >= datetime.combine(date_from, time.min)
            )

        if date_to:
            query = query.filter(
                AuditLog.timestamp <= datetime.combine(date_to, time.max)
            )

        query = query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
