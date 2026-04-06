"""Pruebas unitarias para AuditService."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.audit.services import AuditService
from app.exceptions import NotFoundError
from app.models.audit_log import AuditLog


class TestAuditService:
    """Valida filtros y utilidades del modulo de auditoria."""

    def test_parse_date_valid_and_invalid(self):
        assert AuditService.parse_date("2026-04-05") is not None
        assert AuditService.parse_date("fecha-invalida") is None
        assert AuditService.parse_date("") is None

    def test_get_by_id_not_found_raises(self, app, db_session):
        with pytest.raises(NotFoundError):
            AuditService.get_by_id(999999)

    def test_get_logs_filters(self, app, db_session, seed_basic_data):
        user = seed_basic_data["user"]
        now = datetime.now()

        db_session.add_all(
            [
                AuditLog(
                    table_name="sales",
                    action="INSERT",
                    user_id=user.id,
                    source="db_trigger",
                    record_id="101",
                    timestamp=now,
                    previous_data=None,
                    new_data={"id": 101},
                ),
                AuditLog(
                    table_name="products",
                    action="UPDATE",
                    user_id=user.id,
                    source="application",
                    record_id="202",
                    timestamp=now - timedelta(days=1),
                    previous_data={"id": 202, "price": 100},
                    new_data={"id": 202, "price": 120},
                ),
            ]
        )
        db_session.commit()

        insert_logs = AuditService.get_logs(action="INSERT", page=1, per_page=20)
        assert insert_logs.total >= 1
        assert all(item.action == "INSERT" for item in insert_logs.items)

        trigger_logs = AuditService.get_logs(source="db_trigger", page=1, per_page=20)
        assert trigger_logs.total >= 1
        assert all(item.source == "db_trigger" for item in trigger_logs.items)

        search_logs = AuditService.get_logs(search_term="202", page=1, per_page=20)
        assert search_logs.total >= 1
        assert any(item.record_id == "202" for item in search_logs.items)

    def test_get_filter_options(self, app, db_session, seed_basic_data):
        user = seed_basic_data["user"]

        db_session.add(
            AuditLog(
                table_name="orders",
                action="UPDATE",
                user_id=user.id,
                source="application",
                record_id="33",
                previous_data={"status": "pendiente"},
                new_data={"status": "cancelado"},
            )
        )
        db_session.commit()

        options = AuditService.get_filter_options()

        assert "orders" in options["table_names"]
        assert "UPDATE" in options["actions"]
        assert "application" in options["sources"]
        assert any(item[0] == user.id for item in options["users"])
