from ..extensions import db
from .audit_mixin import AuditMixin


class ProductionOrder(AuditMixin, db.Model):
    """Modelo para la tabla production_orders."""

    __tablename__ = "production_orders"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    is_special_request = db.Column(db.Boolean, nullable=False, default=False)
    do_not_add_to_finished_stock = db.Column(db.Boolean, nullable=False, default=False)
    special_notes = db.Column(db.Text, nullable=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # FK hacia la orden de cliente que originó esta orden de producción
    customer_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)

    product = db.relationship("Product", back_populates="production_orders")
    customer_order = db.relationship(
        "Order", back_populates="production_orders", foreign_keys=[customer_order_id]
    )
    assigned_user = db.relationship(
        "User", foreign_keys=[assigned_user_id], lazy="joined"
    )
    material_consumptions = db.relationship(
        "ProductionOrderMaterial",
        back_populates="production_order",
        lazy=True,
        cascade="all, delete-orphan",
    )

    VALID_STATUSES = (
        "pendiente",
        "en_proceso",
        "terminado",
        "cancelado",
    )

    STATUS_TRANSITIONS: dict = {
        "pendiente": ("en_proceso", "cancelado"),
        "en_proceso": ("terminado", "cancelado"),
        "terminado": (),
        "cancelado": (),
    }

    def can_transition_to(self, new_status: str) -> bool:
        """Valida si el cambio de estado solicitado es permitido."""
        return new_status in self.STATUS_TRANSITIONS.get(self.status, ())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "status": self.status,
            "scheduled_date": (
                self.scheduled_date.isoformat() if self.scheduled_date else None
            ),
            "is_special_request": self.is_special_request,
            "do_not_add_to_finished_stock": self.do_not_add_to_finished_stock,
            "special_notes": self.special_notes,
            "assigned_user_id": self.assigned_user_id,
            **self._audit_dict(),
            "customer_order_id": self.customer_order_id,
        }
