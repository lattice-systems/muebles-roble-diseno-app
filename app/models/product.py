from ..extensions import db
from .audit_mixin import AuditMixin


class Product(AuditMixin, db.Model):
    """Modelo para la tabla products."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    furniture_type_id = db.Column(
        db.Integer, db.ForeignKey("furniture_types.id"), nullable=False
    )
    description = db.Column(db.Text, nullable=True)
    specifications = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.Boolean, nullable=False, default=True)

    furniture_type = db.relationship("FurnitureType", back_populates="products")
    colors = db.relationship("ProductColor", back_populates="product", lazy=True)
    inventory_records = db.relationship(
        "ProductInventory", back_populates="product", lazy=True
    )
    boms = db.relationship("Bom", back_populates="product", lazy=True)
    production_orders = db.relationship(
        "ProductionOrder", back_populates="product", lazy=True
    )
    sale_items = db.relationship("SaleItem", back_populates="product", lazy=True)
    order_items = db.relationship("OrderItem", back_populates="product", lazy=True)

    images = db.relationship(
        "ProductImage",
        back_populates="product",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "furniture_type_id": self.furniture_type_id,
            "description": self.description,
            "specifications": self.specifications,
            "price": float(self.price) if self.price is not None else None,
            "status": self.status,
            **self._audit_dict(),
        }
