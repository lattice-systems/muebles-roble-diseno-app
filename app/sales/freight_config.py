"""
Configuración y cálculo de tarifas de flete para Roble y Diseño.

Sucursal única: León, Guanajuato.
- Envío local  (León, Gto.):  $250 MXN — GRATIS a partir de $5,000
- Envío nacional (resto MX):  $650 MXN — GRATIS a partir de $15,000
"""

from decimal import Decimal

# ── Tarifas ──────────────────────────────────────────────────────
LOCAL_FREIGHT_COST = Decimal("250.00")
NATIONAL_FREIGHT_COST = Decimal("650.00")

LOCAL_FREE_THRESHOLD = Decimal("5000.00")
NATIONAL_FREE_THRESHOLD = Decimal("15000.00")

# Ciudad y estado de la sucursal (en minúsculas para comparación)
STORE_CITY = "león"
STORE_STATE = "guanajuato"


def calculate_freight(customer, cart_subtotal: Decimal) -> dict:
    """
    Calcula el costo de flete según la dirección del cliente y el subtotal del carrito.

    Args:
        customer: Objeto Customer (o None).
        cart_subtotal: Subtotal de productos en el carrito (Decimal).

    Returns:
        dict con:
            - cost (float): Costo de flete a cobrar.
            - zone (str|None): "local" | "nacional" | None.
            - free (bool): True si el envío es gratis.
            - reason (str): Descripción legible del resultado.
    """
    if not customer or not customer.requires_freight:
        return {
            "cost": 0.0,
            "zone": None,
            "free": False,
            "reason": "Sin flete (recoge en sucursal)",
        }

    # Normalizar ciudad y estado del cliente
    customer_city = (customer.city or "").strip().lower()
    customer_state = (customer.state or "").strip().lower()

    is_local = customer_city == STORE_CITY and customer_state == STORE_STATE

    if is_local:
        zone = "local"
        base_cost = LOCAL_FREIGHT_COST
        threshold = LOCAL_FREE_THRESHOLD
    else:
        zone = "nacional"
        base_cost = NATIONAL_FREIGHT_COST
        threshold = NATIONAL_FREE_THRESHOLD

    if cart_subtotal >= threshold:
        return {
            "cost": 0.0,
            "zone": zone,
            "free": True,
            "reason": f"Envío {zone} GRATIS (compra ≥ ${threshold:,.0f})",
        }

    return {
        "cost": float(base_cost),
        "zone": zone,
        "free": False,
        "reason": f"Envío {zone}: ${base_cost:,.2f}",
    }
