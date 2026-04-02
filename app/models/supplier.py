from sqlalchemy.orm import synonym

from ..extensions import db
from .audit_mixin import AuditMixin


class Supplier(AuditMixin, db.Model):
    """Modelo para la tabla suppliers."""

    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    address = db.Column(db.Text, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")

    raw_materials = db.relationship("RawMaterial", back_populates="supplier", lazy=True)

    purchase_orders = db.relationship(
        "PurchaseOrder", back_populates="supplier", lazy=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "status": self.status,
            "active": self.active,
            **self._audit_dict(),
        }
