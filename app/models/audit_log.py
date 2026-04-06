from ..extensions import db


class AuditLog(db.Model):
    """Modelo para la tabla audit_log."""

    __tablename__ = "audit_log"
    __table_args__ = (
        db.Index("ix_audit_log_timestamp", "timestamp"),
        db.Index("ix_audit_log_table_timestamp", "table_name", "timestamp"),
        db.Index("ix_audit_log_user_timestamp", "user_id", "timestamp"),
    )

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    record_id = db.Column(db.String(100), nullable=True)
    source = db.Column(
        db.String(30),
        nullable=False,
        default="application",
        server_default="application",
    )
    timestamp = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    previous_data = db.Column(db.JSON, nullable=True)
    new_data = db.Column(db.JSON, nullable=True)

    user = db.relationship(
        "User", back_populates="audit_logs", foreign_keys="AuditLog.user_id"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "table_name": self.table_name,
            "action": self.action,
            "user_id": self.user_id,
            "record_id": self.record_id,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "previous_data": self.previous_data,
            "new_data": self.new_data,
        }
