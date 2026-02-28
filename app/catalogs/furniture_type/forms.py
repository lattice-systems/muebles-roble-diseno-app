"""
Formularios para el módulo de tipo de mueble.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class FurnitureTypeForm(FlaskForm):
    """Formulario para crear un tipo de mueble."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre del tipo de mueble es requerido"),
            Length(max=50, message="El nombre no puede exceder 50 caracteres"),
        ],
    )
