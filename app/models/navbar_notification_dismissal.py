from ..extensions import db


class NavbarNotificationDismissal(db.Model):
    """Notificaciones descartadas por usuario para la campana del navbar."""

    __tablename__ = "navbar_notification_dismissals"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "source_kind",
            "source_id",
            name="uq_navbar_notification_dismissal_user_source",
        ),
        db.Index(
            "ix_navbar_notification_dismissals_user_timestamp",
            "user_id",
            "dismissed_at",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source_kind = db.Column(db.String(20), nullable=False)
    source_id = db.Column(db.Integer, nullable=False)
    dismissed_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    user = db.relationship(
        "User",
        back_populates="notification_dismissals",
        foreign_keys=[user_id],
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "dismissed_at": (
                self.dismissed_at.isoformat() if self.dismissed_at else None
            ),
        }
