from ..extensions import db


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    product = db.relationship("Product", back_populates="images")
