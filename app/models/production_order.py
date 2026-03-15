from ..extensions import db


class ProductionOrder(db.Model):
    """Modelo para la tabla production_orders."""

    __tablename__ = "production_orders"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)

    product = db.relationship("Product", back_populates="production_orders")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "status": self.status,
            "scheduled_date": (
                self.scheduled_date.isoformat() if self.scheduled_date else None
            ),
        }
