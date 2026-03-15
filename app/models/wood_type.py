from sqlalchemy.orm import synonym

from ..extensions import db


class WoodType(db.Model):
    """Modelo para la tabla wood_types."""

    __tablename__ = "wood_types"

    id = db.Column(db.Integer, primary_key=True)
    id_wood_type = synonym("id")
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_wood_type": self.id_wood_type,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
