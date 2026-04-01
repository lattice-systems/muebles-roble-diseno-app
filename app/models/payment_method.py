from sqlalchemy.orm import synonym

from ..extensions import db
from .audit_mixin import AuditMixin


class PaymentMethod(AuditMixin, db.Model):
    """Modelo para la tabla payment_methods."""

    __tablename__ = "payment_methods"

    id = db.Column(db.Integer, primary_key=True)
    id_payment_method = synonym("id")
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")
    available_pos = db.Column(db.Boolean, nullable=False, default=True)
    available_ecommerce = db.Column(db.Boolean, nullable=False, default=True)

    sales = db.relationship("Sale", back_populates="payment_method", lazy=True)
    orders = db.relationship("Order", back_populates="payment_method", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_payment_method": self.id_payment_method,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": self.status,
            "active": self.active,
            "available_pos": self.available_pos,
            "available_ecommerce": self.available_ecommerce,
            **self._audit_dict(),
        }
