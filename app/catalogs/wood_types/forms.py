"""
Formularios para el módulo de tipos de madera.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp


class WoodTypeForm(FlaskForm):
    """Formulario para crear un tipo de madera."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre del tipo de madera es requerido"),
            Length(min=3, max=50, message="El nombre no puede exceder 50 caracteres"),
            Regexp(
                r"^[a-zA-Z0-9\sáéíóúÁÉÍÓÚñÑ.,\-_]+$",
                message="El nombre solo puede contener letras, números, espacios y caracteres básicos (.,-_)",
            ),
        ],
    )
    description = StringField(
        "Descripción",
        validators=[
            Length(max=200, message="La descripción no puede exceder 200 caracteres"),
            Regexp(
                r"^[a-zA-Z0-9\sáéíóúÁÉÍÓÚñÑ.,\-_]*$",
                message="La descripción solo puede contener letras, números, espacios y caracteres básicos (.,-_)",
            ),
        ],
    )
