"""
Formularios para el módulo de unidades de medida.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField
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
        ],
    )
    type = SelectField(
        "Tipo",
        choices=[
            ("longitud", "Longitud"),
            ("peso", "Peso"),
            ("volumen", "Volumen"),
            ("unidad", "Unidad"),
        ],
        validators=[DataRequired(message="El tipo de unidad es requerido")],
    )
    active = BooleanField("Activo", default=True)
