from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    SelectMultipleField,
    DecimalField,
    IntegerField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProductForm(FlaskForm):
    sku = StringField("SKU", validators=[DataRequired(), Length(min=2, max=50)])

    name = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=120)])

    furniture_type_id = SelectField(
        "Tipo de mueble", coerce=int, validators=[DataRequired()]
    )

    description = TextAreaField("Descripción", validators=[Optional(), Length(max=500)])

    price = DecimalField(
        "Precio", places=2, validators=[DataRequired(), NumberRange(min=0)]
    )

    color_ids = SelectMultipleField("Colores", coerce=int, validators=[Optional()])

    stock = IntegerField("Stock inicial", validators=[Optional(), NumberRange(min=0)])

    status = BooleanField("Activo", default=True)

    submit = SubmitField("Guardar")
