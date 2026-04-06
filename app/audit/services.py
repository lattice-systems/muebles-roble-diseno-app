"""Servicios para consulta del modulo de auditoria."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import joinedload

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Servicio para consultas y filtros de auditoria."""

    ACTION_LABELS = {
        "INSERT": "Creacion",
        "UPDATE": "Actualizacion",
        "DELETE": "Eliminacion",
    }

    SOURCE_LABELS = {
        "db_trigger": "Automatico del sistema",
        "application": "Registrado por aplicacion",
    }

    FIELD_LABELS = {
        "id": "ID",
        "created_at": "Fecha de creacion",
        "updated_at": "Fecha de actualizacion",
        "created_by": "Creado por",
        "updated_by": "Actualizado por",
        "deactivated_by": "Desactivado por",
        "deactivated_at": "Fecha de desactivacion",
        "status": "Estado",
        "active": "Activo",
        "sale_date": "Fecha de venta",
        "order_date": "Fecha de orden",
    }

    SENSITIVE_FIELDS = {
        "password",
        "password_hash",
        "fs_uniquifier",
        "tf_totp_secret",
    }

    SENSITIVE_FIELD_HINTS = (
        "password",
        "secret",
        "token",
        "api_key",
        "private_key",
        "uniquifier",
    )

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
            AuditLog.query.options(joinedload(AuditLog.user).joinedload(User.role))
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
        query = AuditLog.query.options(joinedload(AuditLog.user).joinedload(User.role))

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

    @staticmethod
    def get_action_label(action: str | None) -> str:
        code = (action or "").strip().upper()
        if not code:
            return "Sin accion"
        return AuditService.ACTION_LABELS.get(code, code)

    @staticmethod
    def get_source_label(source: str | None) -> str:
        code = (source or "").strip().lower()
        if not code:
            return "Origen no definido"
        return AuditService.SOURCE_LABELS.get(code, code.replace("_", " ").title())

    @staticmethod
    def _safe_payload(data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def _resolve_record_id(entry: AuditLog) -> str:
        if entry.record_id:
            return str(entry.record_id)

        payload = AuditService._safe_payload(entry.new_data)
        if payload.get("id") is not None:
            return str(payload["id"])

        payload = AuditService._safe_payload(entry.previous_data)
        if payload.get("id") is not None:
            return str(payload["id"])

        return "-"

    @staticmethod
    def _get_actor_name(entry: AuditLog) -> str:
        if entry.user and entry.user.full_name:
            return entry.user.full_name
        if entry.user_id:
            return f"Usuario #{entry.user_id}"
        return "Sistema"

    @staticmethod
    def _get_actor_role(entry: AuditLog) -> str:
        if entry.user and entry.user.role and entry.user.role.name:
            return entry.user.role.name
        if entry.user_id:
            return "Sin rol disponible"
        return "Sistema"

    @staticmethod
    def _field_label(field_key: str) -> str:
        if field_key in AuditService.FIELD_LABELS:
            return AuditService.FIELD_LABELS[field_key]
        return field_key.replace("_", " ").strip().capitalize()

    @staticmethod
    def _is_sensitive_field(field_key: str) -> bool:
        key = (field_key or "").strip().lower()
        if not key:
            return False

        if key in AuditService.SENSITIVE_FIELDS:
            return True

        return any(hint in key for hint in AuditService.SENSITIVE_FIELD_HINTS)

    @staticmethod
    def _redacted_value(value: Any) -> str:
        if value is None:
            return "-"
        return "Oculto (dato sensible)"

    @staticmethod
    def _sanitize_payload(data: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}

        for key, value in data.items():
            if AuditService._is_sensitive_field(key):
                sanitized[key] = "[REDACTED]"
                continue

            if isinstance(value, dict):
                sanitized[key] = AuditService._sanitize_payload(value)
                continue

            if isinstance(value, list):
                sanitized[key] = [
                    (
                        AuditService._sanitize_payload(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
                continue

            sanitized[key] = value

        return sanitized

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "Si" if value else "No"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (dict, list)):
            json_value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            if len(json_value) > 160:
                return f"{json_value[:157]}..."
            return json_value
        text = str(value)
        if len(text) > 160:
            return f"{text[:157]}..."
        return text

    @staticmethod
    def build_change_rows(entry: AuditLog) -> list[dict[str, Any]]:
        action_code = (entry.action or "").strip().upper()
        previous_data = AuditService._safe_payload(entry.previous_data)
        new_data = AuditService._safe_payload(entry.new_data)

        if action_code == "INSERT":
            keys = sorted(new_data.keys())
        elif action_code == "DELETE":
            keys = sorted(previous_data.keys())
        else:
            keys = sorted(set(previous_data.keys()) | set(new_data.keys()))

        rows: list[dict[str, Any]] = []
        for key in keys:
            old_value = previous_data.get(key)
            new_value = new_data.get(key)
            is_sensitive = AuditService._is_sensitive_field(key)

            if action_code == "INSERT":
                old_value = None
            elif action_code == "DELETE":
                new_value = None

            changed = old_value != new_value
            if action_code == "UPDATE" and not changed:
                continue

            if is_sensitive:
                previous_display = AuditService._redacted_value(old_value)
                new_display = AuditService._redacted_value(new_value)
                safe_previous_value = None
                safe_new_value = None
            else:
                previous_display = AuditService._format_value(old_value)
                new_display = AuditService._format_value(new_value)
                safe_previous_value = old_value
                safe_new_value = new_value

            rows.append(
                {
                    "field_key": key,
                    "field_label": AuditService._field_label(key),
                    "previous_value": safe_previous_value,
                    "new_value": safe_new_value,
                    "previous_display": previous_display,
                    "new_display": new_display,
                    "changed": changed,
                    "is_sensitive": is_sensitive,
                }
            )

        return rows

    @staticmethod
    def to_list_item(entry: AuditLog) -> dict[str, Any]:
        action_code = (entry.action or "").strip().upper()
        source_code = (entry.source or "").strip().lower()

        return {
            "id": entry.id,
            "timestamp": entry.timestamp,
            "table_name": entry.table_name,
            "action_code": action_code,
            "action_label": AuditService.get_action_label(action_code),
            "record_id": AuditService._resolve_record_id(entry),
            "actor_name": AuditService._get_actor_name(entry),
            "actor_role": AuditService._get_actor_role(entry),
            "source_code": source_code,
            "source_label": AuditService.get_source_label(source_code),
        }

    @staticmethod
    def to_detail_view(entry: AuditLog) -> dict[str, Any]:
        base = AuditService.to_list_item(entry)
        rows = AuditService.build_change_rows(entry)
        action_code = base["action_code"]

        if action_code == "INSERT":
            change_title = "Datos creados"
        elif action_code == "DELETE":
            change_title = "Datos eliminados"
        else:
            change_title = "Campos modificados"

        base.update(
            {
                "change_title": change_title,
                "changes": rows,
                "has_changes": len(rows) > 0,
                "changes_count": len(rows),
                "previous_raw": AuditService._sanitize_payload(
                    AuditService._safe_payload(entry.previous_data)
                ),
                "new_raw": AuditService._sanitize_payload(
                    AuditService._safe_payload(entry.new_data)
                ),
            }
        )
        return base
