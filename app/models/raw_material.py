from ..extensions import db


class RawMaterial(db.Model):
    """Modelo para la tabla raw_materials."""

    __tablename__ = "raw_materials"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)
    waste_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    stock = db.Column(db.Numeric(12, 3), nullable=False, default=0)

    unit = db.relationship("UnitOfMeasure", back_populates="raw_materials")
    movements = db.relationship(
        "RawMaterialMovement", back_populates="raw_material", lazy=True
    )
    purchase_order_items = db.relationship(
        "PurchaseOrderItem", back_populates="raw_material", lazy=True
    )
    bom_items = db.relationship("BomItem", back_populates="raw_material", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "unit_id": self.unit_id,
            "waste_percentage": (
                float(self.waste_percentage)
                if self.waste_percentage is not None
                else None
            ),
            "stock": float(self.stock) if self.stock is not None else None,
        }
