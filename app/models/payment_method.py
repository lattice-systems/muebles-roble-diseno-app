from sqlalchemy.orm import synonym

from ..extensions import db


class PaymentMethod(db.Model):
    """Modelo para la tabla payment_methods."""

    __tablename__ = "payment_methods"

    id = db.Column(db.Integer, primary_key=True)
    id_payment_method = synonym("id")
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")
    available_pos = db.Column(db.Boolean, nullable=False, default=True)
    available_ecommerce = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    sales = db.relationship("Sale", back_populates="payment_method", lazy=True)
    orders = db.relationship("Order", back_populates="payment_method", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_payment_method": self.id_payment_method,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": self.status,
            "active": self.active,
            "available_pos": self.available_pos,
            "available_ecommerce": self.available_ecommerce,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
