from ..extensions import db
from .audit_mixin import AuditMixin


class Order(AuditMixin, db.Model):
    """Modelo para la tabla orders."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    order_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    status = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_method_id = db.Column(
        db.Integer, db.ForeignKey("payment_methods.id"), nullable=True
    )

    customer = db.relationship("Customer", back_populates="orders")
    payment_method = db.relationship("PaymentMethod", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "status": self.status,
            "total": float(self.total) if self.total is not None else None,
            "payment_method_id": self.payment_method_id,
            **self._audit_dict(),
        }
