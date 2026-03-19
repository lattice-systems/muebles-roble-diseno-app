from flask_security import RoleMixin
from sqlalchemy.orm import synonym

from ..extensions import db


class Role(db.Model, RoleMixin):
    """Modelo para la tabla roles."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    id_role = synonym("id")
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    users = db.relationship("User", back_populates="role", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_role": self.id_role,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
