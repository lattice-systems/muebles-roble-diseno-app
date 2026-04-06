"""
Formularios para el módulo de materias primas.
"""

from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class RawMaterialForm(FlaskForm):
    """Formulario principal para Materia Prima. Note que el stock
    y cost_estimated ya no son gestionados desde aquí."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre es obligatorio"),
            Length(max=150, message="El nombre no puede exceder los 150 caracteres"),
        ],
    )

    description = TextAreaField(
        "Descripción",
        validators=[
            Optional(),
            Length(
                max=500, message="La descripción no puede exceder los 500 caracteres"
            ),
        ],
    )

    category_id = SelectField(
        "Categoría",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar una categoría")],
    )

    unit_id = SelectField(
        "Unidad de Medida base",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar una unidad de medida")],
    )

    waste_percentage = DecimalField(
        "Porcentaje de Merma Estimado (%)",
        places=2,
        default=0.00,
        validators=[
            DataRequired(message="El porcentaje de merma es obligatorio"),
            NumberRange(min=0, max=100, message="La merma debe estar entre 0% y 100%"),
        ],
    )

    minimum_stock = DecimalField(
        "Stock Mínimo Ideal",
        places=3,
        default=10.000,
        validators=[
            DataRequired(message="El stock mínimo es obligatorio"),
            NumberRange(min=0, message="El stock mínimo no puede ser negativo"),
        ],
    )

    status = SelectField(
        "Estado",
        choices=[("active", "Activo"), ("inactive", "Inactivo")],
        default="active",
        validators=[DataRequired(message="El estado es obligatorio")],
    )


class StockAdjustmentForm(FlaskForm):
    """Formulario para ajustes manuales de stock y auditoría de merma."""

    movement_type = SelectField(
        "Tipo de Movimiento",
        choices=[
            ("MERMA", "Merma operativa o deterioro (Salida)"),
            ("AJUSTE_ENTRADA", "Sobrante por inventario físico (Entrada)"),
            ("AJUSTE_SALIDA", "Faltante por inventario físico / Robo (Salida)"),
        ],
        validators=[DataRequired(message="El tipo de movimiento es obligatorio")],
    )

    quantity = DecimalField(
        "Cantidad",
        places=3,
        validators=[
            DataRequired(message="La cantidad es obligatoria"),
            NumberRange(min=0.001, message="La cantidad debe ser mayor a 0"),
        ],
    )

    reason = TextAreaField(
        "Motivo",
        validators=[
            DataRequired(message="El motivo del ajuste es obligatorio para auditoría"),
            Length(max=255, message="El motivo no puede exceder los 255 caracteres"),
        ],
    )
