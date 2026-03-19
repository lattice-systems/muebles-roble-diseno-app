from ..extensions import db


class RawMaterialMovement(db.Model):
    """Modelo para la tabla raw_material_movements."""

    __tablename__ = "raw_material_movements"

    id = db.Column(db.Integer, primary_key=True)
    raw_material_id = db.Column(
        db.Integer, db.ForeignKey("raw_materials.id"), nullable=False
    )
    movement_type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    reference = db.Column(db.String(100), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    raw_material = db.relationship("RawMaterial", back_populates="movements")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "raw_material_id": self.raw_material_id,
            "movement_type": self.movement_type,
            "quantity": float(self.quantity) if self.quantity is not None else None,
            "reason": self.reason,
            "reference": self.reference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
