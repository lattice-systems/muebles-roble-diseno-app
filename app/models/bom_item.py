from ..extensions import db


class BomItem(db.Model):
    """Modelo para la tabla bom_items."""

    __tablename__ = "bom_items"

    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey("bom.id"), nullable=False)
    raw_material_id = db.Column(
        db.Integer, db.ForeignKey("raw_materials.id"), nullable=False
    )
    quantity_required = db.Column(db.Numeric(12, 3), nullable=False)

    bom = db.relationship("Bom", back_populates="items")
    raw_material = db.relationship("RawMaterial", back_populates="bom_items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bom_id": self.bom_id,
            "raw_material_id": self.raw_material_id,
            "quantity_required": (
                float(self.quantity_required)
                if self.quantity_required is not None
                else None
            ),
        }
