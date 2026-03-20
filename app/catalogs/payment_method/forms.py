"""
Formularios para el módulo de métodos de pago.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class PaymentMethodForm(FlaskForm):
    """Formulario para crear/editar un método de pago."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre del método de pago es requerido"),
            Length(
                min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres"
            ),
            Regexp(
                r"^[A-Za-zÀ-ÿ0-9\s\-\.]+$",
                message="El nombre solo puede contener letras, números, espacios, guiones y puntos",
            ),
        ],
    )

    type = SelectField(
        "Tipo",
        choices=[
            ("efectivo", "Efectivo"),
            ("transferencia", "Transferencia"),
            ("tarjeta", "Tarjeta"),
            ("pasarela_online", "Pasarela Online"),
        ],
        validators=[DataRequired(message="El tipo de método de pago es requerido")],
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

    available_pos = BooleanField("Disponible en Ventas Físicas (POS)")
    available_ecommerce = BooleanField("Disponible en Ecommerce")