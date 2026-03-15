from ..extensions import db


class SaleItem(db.Model):
    """Modelo para la tabla sale_items."""

    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", back_populates="sale_items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": float(self.price) if self.price is not None else None,
        }
