from sqlalchemy.orm import synonym

from ..extensions import db
from .audit_mixin import AuditMixin


class Color(AuditMixin, db.Model):
    """Modelo para la tabla colors."""

    __tablename__ = "colors"

    id = db.Column(db.Integer, primary_key=True)
    id_color = synonym("id")
    name = db.Column(db.String(100), nullable=False, unique=True)
    hex_code = db.Column(db.String(7), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")

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
            **self._audit_dict(),
        }
