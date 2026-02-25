"""
Formularios para el módulo de tipos de madera.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class WoodTypeForm(FlaskForm):
    """Formulario para crear un tipo de madera."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre del tipo de madera es requerido"),
            Length(min=3, max=50, message="El nombre no puede exceder 50 caracteres"),
        ],
    )
    description = StringField(
        "Descripción",
        validators=[
            Length(max=200, message="La descripción no puede exceder 200 caracteres"),
        ],
    )
