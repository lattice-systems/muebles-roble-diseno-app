from sqlalchemy.sql import func
from ..extensions import db


class WoodType(db.Model):
    """
    Modelo de Tipo de Madera para catálogo de tipos de madera.

    Attributes:
        id_wood_type: Identificador único del tipo de madera.
        name: Nombre del tipo de madera.
        description: Descripción opcional del tipo de madera.
        active: Indica si el tipo de madera está activo o no.

        created_at: Fecha de creación.
        updated_at: Fecha de última actualización.
        deleted_at: Fecha de eliminación lógica.

        created_by: Usuario que creó el registro.
        updated_by: Usuario que actualizó el registro.
        deleted_by: Usuario que eliminó el registro.
    """

    __tablename__ = 'wood_types'

    id_wood_type = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp()
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp()
    )
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)

    created_by = db.Column(db.String(100), nullable=True)
    updated_by = db.Column(db.String(100), nullable=True)
    deleted_by = db.Column(db.String(100), nullable=True)
    
    def to_dict(self):
        return {
        "id_wood_type": self.id_wood_type,
        "name": self.name,
        "description": self.description,
        "active": self.active,
        "created_at": self.created_at,
        "updated_at": self.updated_at,
        "deleted_at": self.deleted_at,
    }