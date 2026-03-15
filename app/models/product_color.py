from ..extensions import db


class ProductColor(db.Model):
    """Modelo para la tabla product_colors."""

    __tablename__ = "product_colors"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey("colors.id"), nullable=False)

    product = db.relationship("Product", back_populates="colors")
    color = db.relationship("Color", back_populates="product_colors")

    __table_args__ = (
        db.UniqueConstraint("product_id", "color_id", name="uq_product_color"),
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "product_id": self.product_id, "color_id": self.color_id}
