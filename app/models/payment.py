from ..extensions import db
from .audit_mixin import AuditMixin


class Payment(AuditMixin, db.Model):
    """Modelo para la tabla payments."""

    __tablename__ = "payments"

    id_payment = db.Column(db.Integer, primary_key=True)
    payment_type = db.Column(
        db.Enum("SALE", "ORDER", name="payment_type_enum"),
        nullable=False,
        default="SALE",
    )
    id_sale = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    sale = db.relationship("Sale", backref=db.backref("payments", lazy=True))

    def to_dict(self) -> dict:
        return {
            "id_payment": self.id_payment,
            "payment_type": self.payment_type,
            "id_sale": self.id_sale,
            "amount": float(self.amount) if self.amount is not None else None,
            "payment_date": self.payment_date.isoformat()
            if self.payment_date
            else None,
            **self._audit_dict(),
        }
