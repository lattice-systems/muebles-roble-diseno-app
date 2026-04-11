import uuid

from flask_security import UserMixin
from sqlalchemy.orm import synonym

from ..extensions import db


class CustomerUser(db.Model, UserMixin):
    """Cuenta autenticable para clientes de ecommerce."""

    __tablename__ = "customer_users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    password = synonym("password_hash")
    fs_uniquifier = db.Column(
        db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex
    )
    tf_primary_method = db.Column(db.String(64), nullable=True)
    tf_totp_secret = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    active = synonym("status")

    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    customer = db.relationship(
        "Customer",
        back_populates="customer_user",
        uselist=False,
    )
    orders = db.relationship(
        "Order",
        back_populates="customer_user",
        lazy=True,
    )
    reviews = db.relationship(
        "ProductReview",
        back_populates="customer_user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "status": self.status,
            "has_2fa": bool(self.tf_primary_method and self.tf_totp_secret),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
