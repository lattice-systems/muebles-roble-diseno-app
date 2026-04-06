"""Servicios para consulta de eventos de seguridad."""

from __future__ import annotations

from datetime import date, datetime, time

from app.models.security_event_log import SecurityEventLog


class SecurityAuditService:
    """Servicio para filtros y consultas de security_event_log."""

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

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
