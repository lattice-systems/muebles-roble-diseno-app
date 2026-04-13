"""
Formularios para el módulo de compras.
"""

from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField
from wtforms.validators import DataRequired, NumberRange


class PurchaseOrderForm(FlaskForm):
    """Formulario para la cabecera de la orden de compra."""

    supplier_id = SelectField(
        "Proveedor",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar un proveedor")],
    )

    order_date = DateField(
        "Fecha de la Orden",
        validators=[DataRequired(message="La fecha es requerida")],
    )



class PurchaseOrderItemForm(FlaskForm):
    """
    Subformulario para los ítems de la orden.
    No requiere CSRF porque se usará como subformulario
    y la cabecera ya incluye protección CSRF.
    """

    class Meta:
        csrf = False

    raw_material_id = SelectField(
        "Materia Prima",
        coerce=int,
        validators=[DataRequired(message="Debe seleccionar una materia prima")],
    )

    quantity = DecimalField(
        "Cantidad",
        places=3,
        validators=[
            DataRequired(message="La cantidad es requerida"),
            NumberRange(min=0.001, message="La cantidad debe ser válida"),
        ],
    )

    unit_price = DecimalField(
        "Precio Unitario",
        places=2,
        validators=[
            DataRequired(message="El precio es requerido"),
            NumberRange(min=0.01, message="El precio debe ser mayor a 0"),
        ],
    )
