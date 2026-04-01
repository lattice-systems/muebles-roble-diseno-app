from sqlalchemy.orm import synonym

from ..extensions import db
from .audit_mixin import AuditMixin


class UnitOfMeasure(AuditMixin, db.Model):
    """Modelo para la tabla units."""

    __tablename__ = "units"

    id = db.Column(db.Integer, primary_key=True)
    id_unit_of_measure = synonym("id")
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")

    raw_materials = db.relationship("RawMaterial", back_populates="unit", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_unit_of_measure": self.id_unit_of_measure,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "type": self.type,
            "status": self.status,
            "active": self.active,
            **self._audit_dict(),
        }
