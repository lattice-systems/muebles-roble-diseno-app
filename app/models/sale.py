"""
Modelo para la tabla sales (cabecera de venta POS).
"""

from ..extensions import db
from .audit_mixin import AuditMixin


class Sale(AuditMixin, db.Model):
    """
    Modelo para la tabla sales.

    Attributes:
        id: Identificador único
        sale_date: Fecha de la venta (automática)
        total: Total de la venta
        active: Estado de la venta (True = en proceso, False = cancelada/completada)
        id_customer: Cliente opcional (FK customers.id)
        id_employee: Empleado que abre la venta FK users.id)
        payment_method_id: Método de pago FK payment_methods.id)
    """

    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    id_customer = db.Column(
        db.Integer, db.ForeignKey("customers.id"), nullable=True
    )
    id_employee = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    payment_method_id = db.Column(
        db.Integer, db.ForeignKey("payment_methods.id"), nullable=True
    )

    customer = db.relationship("Customer", backref=db.backref("sales", lazy=True))
    employee = db.relationship(
        "User",
        foreign_keys=[id_employee],
        backref=db.backref("sales_as_employee", lazy=True),
    )
    payment_method = db.relationship("PaymentMethod", back_populates="sales")
    items = db.relationship("SaleItem", back_populates="sale", lazy=True)

    def to_dict(self) -> dict:
        """Serializa el modelo a diccionario."""
        return {
            "id": self.id,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "total": float(self.total) if self.total is not None else None,
            "active": self.active,
            "id_customer": self.id_customer,
            "id_employee": self.id_employee,
            "payment_method_id": self.payment_method_id,
            **self._audit_dict(),
        }
