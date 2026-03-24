from ..extensions import db


class AuditLog(db.Model):
    """Modelo para la tabla audit_log."""

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    previous_data = db.Column(db.JSON, nullable=True)
    new_data = db.Column(db.JSON, nullable=True)

    user = db.relationship("User", back_populates="audit_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "table_name": self.table_name,
            "action": self.action,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "previous_data": self.previous_data,
            "new_data": self.new_data,
        }
