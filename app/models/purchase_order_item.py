from ..extensions import db


class PurchaseOrderItem(db.Model):
    """Modelo para la tabla purchase_order_items."""

    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(
        db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False
    )
    raw_material_id = db.Column(
        db.Integer, db.ForeignKey("raw_materials.id"), nullable=False
    )
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    conversion_factor = db.Column(db.Numeric(12, 3), nullable=False, default=1.0)
    received_quantity = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)

    purchase_order = db.relationship("PurchaseOrder", back_populates="items")
    raw_material = db.relationship("RawMaterial", back_populates="purchase_order_items")

    @property
    def subtotal(self) -> float:
        if self.quantity is None or self.unit_price is None:
            return 0.0
        return float(self.quantity) * float(self.unit_price)

    @property
    def pending_quantity(self) -> float:
        qty = float(self.quantity) if self.quantity is not None else 0.0
        rcv = (
            float(self.received_quantity) if self.received_quantity is not None else 0.0
        )
        return max(0.0, qty - rcv)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "raw_material_id": self.raw_material_id,
            "raw_material_name": self.raw_material.name if self.raw_material else None,
            "quantity": float(self.quantity) if self.quantity is not None else None,
            "conversion_factor": (
                float(self.conversion_factor)
                if self.conversion_factor is not None
                else 1.0
            ),
            "received_quantity": (
                float(self.received_quantity)
                if self.received_quantity is not None
                else 0.0
            ),
            "pending_quantity": self.pending_quantity,
            "unit_price": (
                float(self.unit_price) if self.unit_price is not None else None
            ),
            "subtotal": self.subtotal,
        }
