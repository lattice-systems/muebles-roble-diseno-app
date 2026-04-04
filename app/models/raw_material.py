from ..extensions import db
from .audit_mixin import AuditMixin


class RawMaterial(AuditMixin, db.Model):
    """Modelo para materias primas."""

    __tablename__ = "raw_materials"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    category_id = db.Column(
        db.Integer, db.ForeignKey("material_categories.id"), nullable=False
    )

    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)
    waste_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    stock = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="active")

    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    unit = db.relationship("UnitOfMeasure", back_populates="raw_materials")
    category = db.relationship("MaterialCategory", back_populates="raw_materials")
    movements = db.relationship(
        "RawMaterialMovement", back_populates="raw_material", lazy=True
    )
    purchase_order_items = db.relationship(
        "PurchaseOrderItem", back_populates="raw_material", lazy=True
    )

    bom_items = db.relationship("BomItem", back_populates="raw_material", lazy=True)

    production_order_materials = db.relationship(
        "ProductionOrderMaterial",
        back_populates="raw_material",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "unit_id": self.unit_id,
            "waste_percentage": (
                float(self.waste_percentage)
                if self.waste_percentage is not None
                else None
            ),
            "stock": float(self.stock) if self.stock is not None else None,
            "status": self.status,
            "created_at": (
                self.created_at.isoformat()
                if hasattr(self, "created_at") and self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if hasattr(self, "updated_at") and self.updated_at
                else None
            ),
        }
