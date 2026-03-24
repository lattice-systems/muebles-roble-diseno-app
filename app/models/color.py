from sqlalchemy.orm import synonym

from ..extensions import db


class Color(db.Model):
    """Modelo para la tabla colors."""

    __tablename__ = "colors"

    id = db.Column(db.Integer, primary_key=True)
    id_color = synonym("id")
    name = db.Column(db.String(100), nullable=False, unique=True)
    hex_code = db.Column(db.String(7), nullable=True)
    description = db.Column(db.String(200), nullable=True)
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

    product_colors = db.relationship("ProductColor", back_populates="color", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_color": self.id_color,
            "name": self.name,
            "hex_code": self.hex_code,
            "description": self.description,
            "status": self.status,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
