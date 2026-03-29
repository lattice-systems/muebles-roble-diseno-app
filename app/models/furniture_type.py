from sqlalchemy.orm import synonym

from ..extensions import db


class FurnitureType(db.Model):
    """Modelo para la tabla furniture_types."""

    __tablename__ = "furniture_types"

    id = db.Column(db.Integer, primary_key=True)
    id_furniture_type = synonym("id")
    title = db.Column(db.String(100), nullable=False, unique=True)
    subtitle = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    slug = db.Column(db.String(120), nullable=True, unique=True, index=True)
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

    products = db.relationship("Product", back_populates="furniture_type", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_furniture_type": self.id_furniture_type,
            "title": self.title,
            "subtitle": self.subtitle,
            "image_url": self.image_url,
            "slug": self.slug,
            "status": self.status,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
