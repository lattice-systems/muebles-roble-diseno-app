from ..extensions import db
from .audit_mixin import AuditMixin


class MaterialCategory(AuditMixin, db.Model):
    """Modelo para categorías de materia prima."""

    __tablename__ = "material_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")

    raw_materials = db.relationship(
        "RawMaterial",
        back_populates="category",
        lazy=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            **self._audit_dict(),
        }
