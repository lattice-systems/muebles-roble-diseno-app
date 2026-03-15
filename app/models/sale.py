from ..extensions import db


class Sale(db.Model):
    """Modelo para la tabla sales."""

    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_method_id = db.Column(
        db.Integer, db.ForeignKey("payment_methods.id"), nullable=False
    )

    payment_method = db.relationship("PaymentMethod", back_populates="sales")
    items = db.relationship("SaleItem", back_populates="sale", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "total": float(self.total) if self.total is not None else None,
            "payment_method_id": self.payment_method_id,
        }
