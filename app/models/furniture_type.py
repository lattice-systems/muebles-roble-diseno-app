from sqlalchemy.sql import func

from ..extensions import db


class FurnitureType(db.Model):
    """
    Modelo de Tipo de mueble para catálogo de tipo de mueble.

    Attributes:
          id_furniture_type: Identificador único del tipo de mueble.
          name: Nombre del tipo de mueble.
          active: Indica si el tipo de mueble está activo o no.

          created_at: Fecha de creación del tipo de mueble.
          updated_at: Fecha de última actualización del tipo de mueble.
          deleted_at: Fecha de eliminación lógica del tipo de mueble.

          created_by: Usuario que creó el tipo de mueble.
          updated_by: Usuario que actualizó el tipo de mueble.
          deleted_by: Usuario que eliminó el tipo de mueble.
    """

    __tablename__ = 'furniture_type'

    id_furniture_type = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
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

    def to_dict(self) -> dict:
        """
        Serializa el modelo a diccionario.

        Returns:
            dict: Representación del tipo de mueble en formato diccionario
        """
        return {
            "id_furniture_type": self.id_furniture_type,
            "name": self.name,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
