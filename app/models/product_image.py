from ..extensions import db
from .audit_mixin import AuditMixin


class ProductImage(AuditMixin, db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product", back_populates="images")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "image_path": self.image_path,
            "sort_order": self.sort_order,
            **self._audit_dict(),
        }
