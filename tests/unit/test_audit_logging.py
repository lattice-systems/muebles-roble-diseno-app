"""Pruebas unitarias para helper de auditoria de aplicacion."""

from __future__ import annotations

from app.models.audit_log import AuditLog
from app.shared import audit_logging


class TestAuditLoggingHelper:
    """Valida politica anti-duplicados y fallback de auditoria."""

    def test_should_write_application_audit_in_sqlite(self, app, db_session):
        assert audit_logging.should_write_application_audit() is True

    def test_should_not_write_application_audit_in_mysql_mode(
        self, app, db_session, monkeypatch
    ):
        monkeypatch.setattr(audit_logging, "_get_dialect_name", lambda: "mysql")
        assert audit_logging.should_write_application_audit() is False

    def test_log_application_audit_inserts_when_enabled(self, app, db_session):
        audit_logging.log_application_audit(
            table_name="orders",
            action="update",
            previous_data={"id": 10, "status": "pendiente"},
            new_data={"id": 10, "status": "terminado"},
            user_id=1,
        )
        db_session.commit()

        row = AuditLog.query.filter_by(table_name="orders").first()
        assert row is not None
        assert row.action == "UPDATE"
        assert row.source == "application"
        assert row.record_id == "10"

    def test_log_application_audit_skips_when_mysql(self, app, db_session, monkeypatch):
        monkeypatch.setattr(audit_logging, "_get_dialect_name", lambda: "mysql")

        before_count = AuditLog.query.count()
        audit_logging.log_application_audit(
            table_name="sales",
            action="insert",
            new_data={"id": 99},
            user_id=1,
        )
        db_session.commit()

        after_count = AuditLog.query.count()
        assert after_count == before_count
