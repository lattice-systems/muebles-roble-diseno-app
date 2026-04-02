from ..extensions import db
from .audit_mixin import AuditMixin


class Order(db.Model):
    """Modelo para la tabla orders (Órdenes de Cliente - HU-14)."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    order_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    estimated_delivery_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="pendiente")
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_method_id = db.Column(
        db.Integer, db.ForeignKey("payment_methods.id"), nullable=True
    )
    notes = db.Column(db.Text, nullable=True)
    # source: 'pos' | 'ecommerce' | 'manual'
    source = db.Column(db.String(20), nullable=False, default="manual")

    # Venta POS que originó esta orden (nullable para órdenes manuales/ecommerce)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)

    # Auditoría de creación
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Auditoría de cancelación
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    cancelled_reason = db.Column(db.Text, nullable=True)

    # Relaciones
    customer = db.relationship("Customer", back_populates="orders")
    sale = db.relationship("Sale", backref=db.backref("customer_order", uselist=False))
    payment_method = db.relationship("PaymentMethod", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", lazy=True, cascade="all, delete-orphan"
    )
    created_by = db.relationship(
        "User",
        foreign_keys=[created_by_id],
        backref=db.backref("created_orders", lazy=True),
    )
    cancelled_by = db.relationship(
        "User",
        foreign_keys=[cancelled_by_id],
        backref=db.backref("cancelled_orders", lazy=True),
    )
    production_orders = db.relationship(
        "ProductionOrder", back_populates="customer_order", lazy=True
    )

    # Estados válidos
    VALID_STATUSES = ("pendiente", "en_produccion", "terminado", "entregado", "cancelado")
    VALID_SOURCES = ("pos", "ecommerce", "manual")

    # Transiciones permitidas por estado
    STATUS_TRANSITIONS: dict = {
        "pendiente": ("en_produccion", "cancelado"),
        "en_produccion": ("terminado",),
        "terminado": ("entregado",),
        "entregado": (),
        "cancelado": (),
    }

    def can_cancel(self) -> bool:
        return self.status == "pendiente"

    def can_send_to_production(self) -> bool:
        return self.status == "pendiente"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "estimated_delivery_date": (
                self.estimated_delivery_date.isoformat()
                if self.estimated_delivery_date
                else None
            ),
            "status": self.status,
            "total": float(self.total) if self.total is not None else None,
            "payment_method_id": self.payment_method_id,
            "notes": self.notes,
            "source": self.source,
            "created_by_id": self.created_by_id,
            "cancelled_at": (
                self.cancelled_at.isoformat() if self.cancelled_at else None
            ),
            "cancelled_by_id": self.cancelled_by_id,
            "cancelled_reason": self.cancelled_reason,
            "sale_id": self.sale_id,
            **self._audit_dict(),
        }
