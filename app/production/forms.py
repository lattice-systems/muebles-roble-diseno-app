"""
Formularios para el módulo de Producción y Recetas (BOM).
"""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    SelectField,
    StringField,
    TextAreaField,
)
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

    assigned_user_id = SelectField(
        "Responsable de producción",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar un responsable")],
    )

    is_special_request = BooleanField("Orden especial de cliente")

    do_not_add_to_finished_stock = BooleanField(
        "No ingresar al stock general al terminar"
    )

    special_notes = TextAreaField(
        "Notas especiales",
        validators=[
            Optional(),
            Length(max=1000, message="Las notas no pueden exceder 1000 caracteres"),
        ],
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


class ProductionAssigneeForm(FlaskForm):
    """Formulario para asignar o reasignar responsable de una orden."""

    assigned_user_id = SelectField(
        "Responsable",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar un responsable")],
    )
