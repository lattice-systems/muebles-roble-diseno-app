from ..extensions import db


class ProductionOrderMaterial(db.Model):
    """Consumo planeado y real de materia prima por orden de producción."""

    __tablename__ = "production_order_materials"

    id = db.Column(db.Integer, primary_key=True)

    production_order_id = db.Column(
        db.Integer,
        db.ForeignKey("production_orders.id"),
        nullable=False
    )

    raw_material_id = db.Column(
        db.Integer,
        db.ForeignKey("raw_materials.id"),
        nullable=False
    )

    quantity_planned = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    quantity_used = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    waste_applied = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp()
    )

    production_order = db.relationship(
        "ProductionOrder",
        back_populates="material_consumptions"
    )

    raw_material = db.relationship(
        "RawMaterial",
        back_populates="production_order_materials"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "production_order_id",
            "raw_material_id",
            name="uq_production_order_material"
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "production_order_id": self.production_order_id,
            "raw_material_id": self.raw_material_id,
            "quantity_planned": float(self.quantity_planned)
            if self.quantity_planned is not None else None,
            "quantity_used": float(self.quantity_used)
            if self.quantity_used is not None else None,
            "unit_cost": float(self.unit_cost)
            if self.unit_cost is not None else None,
            "waste_applied": float(self.waste_applied)
            if self.waste_applied is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }