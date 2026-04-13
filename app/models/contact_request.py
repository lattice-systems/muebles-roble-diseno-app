from ..extensions import db
from .audit_mixin import AuditMixin


class ContactRequest(AuditMixin, db.Model):
    """Solicitud comercial para contacto/cita de muebles personalizados."""

    __tablename__ = "contact_requests"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    subject = db.Column(db.String(180), nullable=True)
    message = db.Column(db.Text, nullable=False)

    request_type = db.Column(db.String(30), nullable=False, default="custom_furniture")
    status = db.Column(db.String(30), nullable=False, default="new", index=True)
    source = db.Column(db.String(20), nullable=False, default="ecommerce")
    preferred_datetime = db.Column(db.DateTime, nullable=True)

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer_user_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_users.id"),
        nullable=True,
    )
    converted_order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=True
    )

    internal_notes = db.Column(db.Text, nullable=True)

    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id], lazy="joined")
    customer = db.relationship("Customer", foreign_keys=[customer_id], lazy="joined")
    customer_user = db.relationship(
        "CustomerUser",
        foreign_keys=[customer_user_id],
        lazy="joined",
    )
    converted_order = db.relationship("Order", foreign_keys=[converted_order_id])

    VALID_TYPES = ("custom_furniture", "appointment", "contact")
    TYPE_LABELS = {
        "custom_furniture": "Mueble personalizado",
        "appointment": "Cita",
        "contact": "Contacto",
    }

    VALID_STATUSES = (
        "new",
        "assigned",
        "in_progress",
        "responded",
        "completed",
        "rejected",
    )
    STATUS_LABELS = {
        "new": "Nueva",
        "assigned": "Asignada",
        "in_progress": "En proceso",
        "responded": "Respondida",
        "completed": "Completada",
        "rejected": "Rechazada",
    }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "subject": self.subject,
            "message": self.message,
            "request_type": self.request_type,
            "status": self.status,
            "source": self.source,
            "preferred_datetime": (
                self.preferred_datetime.isoformat() if self.preferred_datetime else None
            ),
            "assigned_to_id": self.assigned_to_id,
            "customer_id": self.customer_id,
            "customer_user_id": self.customer_user_id,
            "converted_order_id": self.converted_order_id,
            "internal_notes": self.internal_notes,
            **self._audit_dict(),
        }
