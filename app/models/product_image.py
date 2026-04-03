from ..extensions import db
from .audit_mixin import AuditMixin


class ProductImage(AuditMixin, db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    public_id = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, nullable=True)

    product = db.relationship("Product", back_populates="images")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "image_url": self.image_url,
            "public_id": self.public_id,
            "sort_order": self.sort_order,
            **self._audit_dict(),
        }
