"""
Prueba E2E: flujo completo de checkout ecommerce.

Simula el viaje del usuario desde la página principal hasta
la confirmación del pedido, pasando por carrito y checkout.
"""

from app.models.order import Order


class TestEcommerceCheckoutFlow:
    """
    Test E2E del flujo completo de compra en ecommerce.

    Pasos:
    1. Entrar al home
    2. Agregar producto al carrito
    3. Ver el carrito
    4. Ir al checkout
    5. Enviar formulario de checkout
    6. Verificar redirección a success
    7. Verificar que la orden existe en BD y carrito vacío
    """

    def test_full_checkout_journey_pickup(
        self, client, app, db_session, seed_basic_data
    ):
        """Flujo completo de checkout con recolección en tienda."""
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]

        # 1. Página principal carga
        resp = client.get("/ecommerce/")
        assert resp.status_code == 200

        # 2. Agregar producto al carrito
        resp = client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 2},
        )
        assert resp.status_code == 302  # redirect

        # 3. Verificar carrito tiene el producto
        resp = client.get("/ecommerce/cart")
        assert resp.status_code == 200
        assert b"Silla" in resp.data or b"silla" in resp.data

        # 4. Ir al checkout
        resp = client.get("/ecommerce/checkout")
        assert resp.status_code == 200

        # 5. Enviar formulario de checkout (pickup = sin envío)
        resp = client.post(
            "/ecommerce/checkout",
            data={
                "first_name": "María",
                "last_name": "López",
                "email": "maria.checkout@test.com",
                "phone": "4771234567",
                "delivery_mode": "pickup",
                "payment_method_id": str(pm.id),
                "notes": "Test E2E checkout",
            },
            follow_redirects=False,
        )

        # 6. Debe redirigir a la página de éxito
        assert resp.status_code == 302
        assert "checkout/success" in resp.headers.get("Location", "")

        # 7. Verificar orden en BD
        with app.app_context():
            order = (
                Order.query.filter_by(source="ecommerce")
                .order_by(Order.id.desc())
                .first()
            )
            assert order is not None
            assert order.status == "pendiente"
            assert len(order.items) == 1
            assert order.items[0].quantity == 2

            # Verificar datos del cliente
            assert order.customer is not None
            assert order.customer.email == "maria.checkout@test.com"

        # 8. Verificar página de éxito carga
        resp = client.get(
            f"/ecommerce/checkout/success?order_id={order.id}",
        )
        assert resp.status_code == 200

        # 9. Verificar que el carrito está vacío después del checkout
        resp = client.get("/ecommerce/cart")
        assert resp.status_code == 200

    def test_full_checkout_journey_shipping(
        self, client, app, db_session, seed_basic_data
    ):
        """Flujo completo de checkout con envío a domicilio."""
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]

        # Agregar producto
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )

        # Checkout con datos de envío
        resp = client.post(
            "/ecommerce/checkout",
            data={
                "first_name": "Carlos",
                "last_name": "Hernández",
                "email": "carlos.e2e@test.com",
                "phone": "4779876543",
                "delivery_mode": "shipping",
                "payment_method_id": str(pm.id),
                "zip_code": "76000",
                "state": "Querétaro",
                "city": "Querétaro",
                "street": "Av. Universidad",
                "neighborhood": "Centro",
                "exterior_number": "100",
                "interior_number": "",
                "notes": "E2E shipping test",
            },
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert "checkout/success" in resp.headers.get("Location", "")

        with app.app_context():
            order = (
                Order.query.filter_by(source="ecommerce")
                .order_by(Order.id.desc())
                .first()
            )
            assert order is not None
            assert order.customer.city == "Querétaro"
            assert order.customer.zip_code == "76000"

    def test_checkout_fails_with_empty_cart(self, client, db_session, seed_basic_data):
        """El checkout falla si el carrito está vacío."""
        pm = seed_basic_data["payment_method"]

        resp = client.post(
            "/ecommerce/checkout",
            data={
                "first_name": "Test",
                "last_name": "Empty",
                "email": "empty@test.com",
                "phone": "1234567890",
                "delivery_mode": "pickup",
                "payment_method_id": str(pm.id),
            },
        )

        assert resp.status_code == 400

    def test_browse_then_search_then_checkout(
        self, client, app, db_session, seed_basic_data
    ):
        """Flujo: buscar → ver producto → agregar → checkout."""
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]

        # Buscar producto
        resp = client.get("/ecommerce/search?q=Silla")
        assert resp.status_code == 200

        # Ver detalle
        resp = client.get(f"/ecommerce/product/{product.id}")
        assert resp.status_code == 200

        # Agregar al carrito
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )

        # Checkout
        resp = client.post(
            "/ecommerce/checkout",
            data={
                "first_name": "Search",
                "last_name": "User",
                "email": "search.user@test.com",
                "phone": "4771112233",
                "delivery_mode": "pickup",
                "payment_method_id": str(pm.id),
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
