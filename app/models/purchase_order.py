from ..extensions import db
from .audit_mixin import AuditMixin


class PurchaseOrder(AuditMixin, db.Model):
    """Modelo para la tabla purchase_orders."""

    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    supplier = db.relationship("Supplier", back_populates="purchase_orders")
    items = db.relationship(
        "PurchaseOrderItem", back_populates="purchase_order", lazy=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "status": self.status,
            "total": float(self.total) if self.total is not None else None,
            **self._audit_dict(),
        }
