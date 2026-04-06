"""Servicios para consulta de eventos de seguridad."""

from __future__ import annotations

from datetime import date, datetime, time

from app.exceptions import NotFoundError
from app.models.security_event_log import SecurityEventLog


class SecurityAuditService:
    """Servicio para filtros y consultas de security_event_log."""

    EVENT_LABELS = {
        "auth.login.success": "Inicio de sesion exitoso",
        "auth.login.failed": "Intento de inicio de sesion fallido",
        "auth.logout": "Cierre de sesion",
        "auth.password.changed": "Cambio de contrasena",
        "auth.password.reset.completed": "Restablecimiento de contrasena",
        "auth.unauthenticated.access": "Intento de acceso sin autenticar",
        "auth.account.locked": "Cuenta bloqueada por intentos",
        "auth.account.unlocked.auto": "Desbloqueo automatico de cuenta",
        "auth.rbac.denied": "Acceso denegado por permisos",
    }

    RESULT_LABELS = {
        "success": "Exito",
        "denied": "Denegado",
        "info": "Informativo",
        "error": "Error",
    }

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def get_by_id(event_id: int) -> SecurityEventLog:
        item = SecurityEventLog.query.filter(SecurityEventLog.id == event_id).first()

        if not item:
            raise NotFoundError(
                f"No se encontro un evento de seguridad con ID {event_id}"
            )

        return item

    @staticmethod
    def get_logs(
        *,
        event_type: str | None = None,
        result: str | None = None,
        search_term: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        query = SecurityEventLog.query

        if event_type:
            query = query.filter(SecurityEventLog.event_type == event_type)

        if result:
            query = query.filter(SecurityEventLog.result == result)

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(
                SecurityEventLog.email_or_identifier.ilike(term)
                | SecurityEventLog.ip_address.ilike(term)
                | SecurityEventLog.reason.ilike(term)
            )

        if date_from:
            query = query.filter(
                SecurityEventLog.timestamp >= datetime.combine(date_from, time.min)
            )

        if date_to:
            query = query.filter(
                SecurityEventLog.timestamp <= datetime.combine(date_to, time.max)
            )

        query = query.order_by(
            SecurityEventLog.timestamp.desc(), SecurityEventLog.id.desc()
        )
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_filter_options() -> dict[str, list[str]]:
        event_types = [
            row[0]
            for row in SecurityEventLog.query.with_entities(SecurityEventLog.event_type)
            .distinct()
            .order_by(SecurityEventLog.event_type.asc())
            .all()
            if row[0]
        ]
        results = [
            row[0]
            for row in SecurityEventLog.query.with_entities(SecurityEventLog.result)
            .distinct()
            .order_by(SecurityEventLog.result.asc())
            .all()
            if row[0]
        ]
        return {"event_types": event_types, "results": results}

    @staticmethod
    def event_label(code: str | None) -> str:
        key = (code or "").strip()
        if not key:
            return "Evento no definido"
        return SecurityAuditService.EVENT_LABELS.get(key, key)

    @staticmethod
    def result_label(code: str | None) -> str:
        key = (code or "").strip().lower()
        if not key:
            return "No definido"
        return SecurityAuditService.RESULT_LABELS.get(key, key.capitalize())

    @staticmethod
    def to_list_item(entry: SecurityEventLog) -> dict:
        return {
            "id": entry.id,
            "timestamp": entry.timestamp,
            "event_type": entry.event_type,
            "event_label": SecurityAuditService.event_label(entry.event_type),
            "result": entry.result,
            "result_label": SecurityAuditService.result_label(entry.result),
            "email_or_identifier": entry.email_or_identifier,
            "user_id": entry.user_id,
            "ip_address": entry.ip_address,
            "reason": entry.reason,
        }

    @staticmethod
    def to_detail_view(entry: SecurityEventLog) -> dict:
        return {
            **SecurityAuditService.to_list_item(entry),
            "context_data": entry.context_data,
            "user_agent": entry.user_agent,
            "source": entry.source,
        }
