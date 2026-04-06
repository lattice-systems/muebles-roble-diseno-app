"""
Formularios para el módulo de tipo de mueble.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Optional, URL


class FurnitureTypeForm(FlaskForm):
    """Formulario para crear un tipo de mueble."""

    title = StringField(
        "Titulo",
        validators=[
            DataRequired(message="El titulo del tipo de mueble es requerido"),
            Length(max=100, message="El titulo no puede exceder 100 caracteres"),
        ],
    )

    subtitle = StringField(
        "Subtitulo",
        validators=[
            Optional(),
            Length(max=255, message="El subtitulo no puede exceder 255 caracteres"),
        ],
    )

    image_url = StringField(
        "URL de imagen",
        validators=[
            Optional(),
            Length(max=500, message="La URL no puede exceder 500 caracteres"),
            URL(message="Ingresa una URL de imagen valida"),
        ],
    )

    image_file = FileField(
        "Imagen",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                "Solo se permiten imagenes JPG, PNG o WEBP",
            ),
        ],
    )
