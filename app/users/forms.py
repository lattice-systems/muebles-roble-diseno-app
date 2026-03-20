"""
Formularios para el módulo de usuarios.
"""

import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Email, Length, ValidationError


class UserForm(FlaskForm):
    """Formulario para crear usuarios."""

    full_name = StringField(
        "Nombre completo",
        validators=[
            DataRequired(message="El nombre completo es requerido"),
            Length(max=150, message="El nombre no puede exceder 150 caracteres"),
        ],
    )

    email = StringField(
        "Correo electrónico",
        validators=[
            DataRequired(message="El correo electrónico es requerido"),
            Email(message="Ingrese un correo electrónico válido"),
            Length(max=120, message="El correo no puede exceder 120 caracteres"),
        ],
    )

    password = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es requerida"),
            Length(min=8, message="La contraseña debe tener al menos 8 caracteres"),
            Length(max=128, message="La contraseña no puede exceder 128 caracteres"),
        ],
    )

    role_id = SelectField(
        "Rol",
        coerce=int,
        validators=[DataRequired(message="Seleccione un rol")],
    )

    status = BooleanField("Usuario activo", default=True)

    def validate_password(self, field) -> None:
        """Valida complejidad de contraseña con un solo mensaje amigable."""
        value = field.data or ""
        if (
            len(value) < 8
            or not re.search(r"[A-Z]", value)
            or not re.search(r"[a-z]", value)
            or not re.search(r"\d", value)
            or not re.search(r"[^A-Za-z0-9]", value)
        ):
            raise ValidationError("La contraseña no cumple los requisitos de seguridad")
