from ..extensions import db


class PaymentMethod(db.Model):
    """Modelo para la tabla payment_methods."""

    __tablename__ = "payment_methods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)

    sales = db.relationship("Sale", back_populates="payment_method", lazy=True)
    orders = db.relationship("Order", back_populates="payment_method", lazy=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.type}
