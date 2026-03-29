from ..extensions import db


class Customer(db.Model):
    """Modelo para la tabla customers."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(75), nullable=False)
    last_name = db.Column(db.String(75), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=False)
    
    # Freight fields
    requires_freight = db.Column(db.Boolean, nullable=False, default=False)
    zip_code = db.Column(db.String(10), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    street = db.Column(db.String(150), nullable=True)
    neighborhood = db.Column(db.String(150), nullable=True)
    exterior_number = db.Column(db.String(20), nullable=True)
    interior_number = db.Column(db.String(20), nullable=True)
    
    status = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )

    orders = db.relationship("Order", back_populates="customer", lazy=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "requires_freight": self.requires_freight,
            "zip_code": self.zip_code,
            "state": self.state,
            "city": self.city,
            "street": self.street,
            "neighborhood": self.neighborhood,
            "exterior_number": self.exterior_number,
            "interior_number": self.interior_number,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
