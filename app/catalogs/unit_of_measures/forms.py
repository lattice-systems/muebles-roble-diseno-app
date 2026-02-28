"""
Formularios para el módulo de unidades de medida.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Length


class UnitOfMeasureForm(FlaskForm):
    """Formulario para crear una unidad de medida."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre de la unidad de medida es requerido"),
            Length(max=50, message="El nombre no puede exceder 50 caracteres"),
        ],
    )
    abbreviation = StringField(
        "Abreviatura",
        validators=[
            DataRequired(message="La abreviatura de la unidad de medida es requerida"),
            Length(max=10, message="La abreviatura no puede exceder 10 caracteres"),
        ]
    )
    active = BooleanField("Activo", default=True)
