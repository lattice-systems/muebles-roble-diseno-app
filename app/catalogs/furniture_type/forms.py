"""
Formularios para el módulo de tipo de mueble.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class FurnitureTypeForm(FlaskForm):
    """Formulario para crear un tipo de mueble."""

    title = StringField(
        "Titulo",
        validators=[
            DataRequired(message="El titulo del tipo de mueble es requerido"),
            Length(max=100, message="El titulo no puede exceder 100 caracteres"),
        ],
    )
