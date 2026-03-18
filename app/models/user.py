import uuid

from flask_security import UserMixin
from sqlalchemy.orm import synonym

from ..extensions import db


class User(db.Model, UserMixin):
    """Modelo para la tabla users."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    password = synonym("password_hash")
    fs_uniquifier = db.Column(
        db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex
    )
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    role = db.relationship("Role", back_populates="users")
    audit_logs = db.relationship("AuditLog", back_populates="user", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role_id": self.role_id,
            "status": self.status,
            "fs_uniquifier": self.fs_uniquifier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
