from ..extensions import db


class ProductReview(db.Model):
    """Reseña/calificación de un producto hecha por un cliente autenticado."""

    __tablename__ = "product_reviews"
    __table_args__ = (
        db.UniqueConstraint(
            "product_id",
            "customer_user_id",
            name="uq_product_reviews_product_customer_user",
        ),
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_product_reviews_rating"
        ),
        db.Index("ix_product_reviews_product_id", "product_id"),
        db.Index("ix_product_reviews_customer_user_id", "customer_user_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    customer_user_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_users.id"),
        nullable=False,
    )
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    product = db.relationship("Product", back_populates="reviews")
    customer_user = db.relationship("CustomerUser", back_populates="reviews")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "customer_user_id": self.customer_user_id,
            "rating": self.rating,
            "review_text": self.review_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
