from ..extensions import db
from .audit_mixin import AuditMixin


class Bom(AuditMixin, db.Model):
    """Modelo para la tabla bom."""

    __tablename__ = "bom"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

    product = db.relationship("Product", back_populates="boms")
    items = db.relationship("BomItem", back_populates="bom", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("product_id", "version", name="uq_bom_product_version"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "version": self.version,
            "description": self.description,
            **self._audit_dict(),
        }
