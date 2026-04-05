"""
Formularios para el módulo de Producción y Recetas (BOM).
"""

from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class BomForm(FlaskForm):
    """Formulario para crear/editar recetas BOM."""

    product_id = SelectField(
        "Producto",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar un producto")],
    )

    version = StringField(
        "Versión",
        validators=[
            DataRequired(message="La versión es obligatoria"),
            Length(max=50, message="La versión no puede exceder 50 caracteres"),
        ],
    )

    description = TextAreaField(
        "Descripción",
        validators=[
            Optional(),
            Length(max=1000, message="La descripción no puede exceder 1000 caracteres"),
        ],
    )


class ProductionOrderForm(FlaskForm):
    """Formulario para crear órdenes de producción manuales."""

    product_id = SelectField(
        "Producto",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar un producto")],
    )

    quantity = IntegerField(
        "Cantidad a producir",
        validators=[
            DataRequired(message="La cantidad es obligatoria"),
            NumberRange(min=1, message="La cantidad debe ser mayor a 0"),
        ],
    )

    scheduled_date = DateField(
        "Fecha programada",
        validators=[DataRequired(message="La fecha programada es obligatoria")],
    )


class ProductionStatusForm(FlaskForm):
    """Formulario para transiciones de estado de órdenes de producción."""

    status = SelectField(
        "Estado",
        choices=[
            ("pendiente", "Pendiente"),
            ("en_proceso", "En Proceso"),
            ("terminado", "Terminado"),
            ("cancelado", "Cancelado"),
        ],
        validators=[DataRequired(message="Debe seleccionar un estado")],
    )
