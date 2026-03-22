"""
Formularios para el módulo de proveedores.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp


class SupplierForm(FlaskForm):
    """Formulario para crear y editar proveedores."""

    name = StringField(
        "Nombre del proveedor",
        validators=[
            DataRequired(message="El nombre del proveedor es requerido"),
            Length(
                min=2, max=150, message="El nombre debe tener entre 2 y 150 caracteres"
            ),
            Regexp(
                r"^[A-Za-zÀ-ÿ0-9\s\-\.\&\,]+$",
                message="El nombre contiene caracteres no permitidos",
            ),
        ],
    )

    phone = StringField(
        "Teléfono",
        validators=[
            Optional(),
            Length(
                min=10, max=10, message="El teléfono debe tener exactamente 10 dígitos"
            ),
            Regexp(
                r"^\d{10}$",
                message="El teléfono debe contener únicamente números",
            ),
        ],
    )

    email = StringField(
        "Correo electrónico",
        validators=[
            Optional(),
            Email(message="Ingrese un correo electrónico válido"),
            Length(max=120, message="El correo no puede exceder 120 caracteres"),
        ],
    )

    address = TextAreaField(
        "Dirección",
        validators=[
            Optional(),
            Length(max=500, message="La dirección no puede exceder 500 caracteres"),
        ],
    )

    status = BooleanField("Proveedor activo", default=True)
