from ..extensions import db


class SecurityEventLog(db.Model):
    """Modelo para la tabla security_event_log."""

    __tablename__ = "security_event_log"
    __table_args__ = (
        db.Index("ix_security_event_log_timestamp", "timestamp"),
        db.Index(
            "ix_security_event_log_event_type_timestamp", "event_type", "timestamp"
        ),
        db.Index("ix_security_event_log_user_timestamp", "user_id", "timestamp"),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(80), nullable=False)
    result = db.Column(
        db.String(20), nullable=False, default="info", server_default="info"
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    email_or_identifier = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    context_data = db.Column(db.JSON, nullable=True)
    source = db.Column(
        db.String(30),
        nullable=False,
        default="application",
        server_default="application",
    )
    timestamp = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    user = db.relationship(
        "User",
        back_populates="security_events",
        foreign_keys="SecurityEventLog.user_id",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "result": self.result,
            "user_id": self.user_id,
            "email_or_identifier": self.email_or_identifier,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "reason": self.reason,
            "context_data": self.context_data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
