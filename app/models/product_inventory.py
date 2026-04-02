from ..extensions import db
from .audit_mixin import AuditMixin


class ProductInventory(AuditMixin, db.Model):
    """Modelo para la tabla product_inventory."""

    __tablename__ = "product_inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

    product = db.relationship("Product", back_populates="inventory_records")

    __table_args__ = (
        db.UniqueConstraint("product_id", name="uq_product_inventory_product"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "stock": self.stock,
            **self._audit_dict(),
        }
