from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class RawMaterialForm(FlaskForm):
    name = StringField(
        "Nombre",
        validators=[DataRequired(), Length(max=150)],
    )

    description = TextAreaField(
        "Descripción",
        validators=[Optional(), Length(max=500)],
    )

    category_id = SelectField(
        "Categoría",
        coerce=int,
        validators=[DataRequired()],
    )

    unit_id = SelectField(
        "Unidad de medida",
        coerce=int,
        validators=[DataRequired()],
    )

    stock = DecimalField(
        "Stock",
        validators=[DataRequired(), NumberRange(min=0)],
        places=3,
    )

    estimated_cost = DecimalField(
        "Costo estimado",
        validators=[Optional(), NumberRange(min=0)],
        places=2,
    )

    waste_percentage = DecimalField(
        "Porcentaje de merma",
        validators=[DataRequired(), NumberRange(min=0, max=100)],
        places=2,
    )

    status = SelectField(
        "Estado",
        choices=[
            ("active", "Activo"),
            ("inactive", "Inactivo"),
        ],
        validators=[DataRequired()],
    )

    supplier_id = SelectField(
        "Proveedor habitual",
        coerce=int,
        validators=[Optional()],
    )

    submit = SubmitField("Guardar")


class StockAdjustmentForm(FlaskForm):
    movement_type = SelectField(
        "Tipo de ajuste",
        choices=[
            ("ADJUSTMENT_IN", "Incremento"),
            ("ADJUSTMENT_OUT", "Decremento"),
        ],
        validators=[DataRequired()],
    )

    quantity = DecimalField(
        "Cantidad",
        validators=[DataRequired(), NumberRange(min=0.001)],
        places=3,
    )

    reason = StringField(
        "Motivo",
        validators=[DataRequired(), Length(max=255)],
    )

    submit = SubmitField("Actualizar stock")


class WasteForm(FlaskForm):
    waste_percentage = DecimalField(
        "Porcentaje de merma",
        validators=[DataRequired(), NumberRange(min=0, max=100)],
        places=2,
    )

    submit = SubmitField("Actualizar merma")