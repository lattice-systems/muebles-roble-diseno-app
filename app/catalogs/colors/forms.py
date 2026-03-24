"""
Formularios para el módulo de colores.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class ColorForm(FlaskForm):
    """Formulario para crear/editar un color."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre del color es requerido"),
            Length(
                min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres"
            ),
            Regexp(
                r"^[A-Za-zÀ-ÿ0-9\s\-\.]+$",
                message="El nombre solo puede contener letras, números, espacios, guiones y puntos",
            ),
        ],
    )

    hex_code = StringField(
        "Código Hexadecimal",
        validators=[
            DataRequired(message="El código hexadecimal es requerido"),
            Regexp(
                r"^#[0-9A-Fa-f]{6}$",
                message="El código hexadecimal debe tener el formato #RRGGBB (ej. #FF5733)",
            ),
        ],
    )

    description = TextAreaField(
        "Descripción",
        validators=[
            Optional(),
            Length(
                max=200,
                message="La descripción no puede exceder 200 caracteres",
            ),
            Regexp(
                r"^[A-Za-zÀ-ÿ0-9\s\-\.\,\;\:]*$",
                message="La descripción contiene caracteres no permitidos",
            ),
        ],
    )
