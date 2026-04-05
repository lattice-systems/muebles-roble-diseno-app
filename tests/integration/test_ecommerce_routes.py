"""
Pruebas de integración para rutas del blueprint ecommerce.

Verifica respuestas HTTP, códigos de estado, y comportamiento
del carrito + checkout vía Flask test client.
"""


class TestEcommercePages:
    """Smoke tests: las páginas principales cargan sin errores."""

    def test_home_page_loads(self, client, db_session, seed_basic_data):
        """GET /ecommerce/ devuelve 200."""
        resp = client.get("/ecommerce/")
        assert resp.status_code == 200

    def test_products_page_loads(self, client, db_session, seed_basic_data):
        """GET /ecommerce/products devuelve 200."""
        resp = client.get("/ecommerce/products")
        assert resp.status_code == 200

    def test_product_detail_exists(self, client, db_session, seed_basic_data):
        """GET /ecommerce/product/{id} devuelve 200 para producto existente."""
        product = seed_basic_data["product"]
        resp = client.get(f"/ecommerce/product/{product.id}")
        assert resp.status_code == 200

    def test_product_detail_nonexistent_redirects(
        self, client, db_session, seed_basic_data
    ):
        """GET /ecommerce/product/99999 redirige al primer producto o 404."""
        resp = client.get("/ecommerce/product/99999")
        # Puede ser 200 (redirect al primer producto) o 404
        assert resp.status_code in (200, 404)

    def test_cart_page_empty(self, client, db_session, seed_basic_data):
        """GET /ecommerce/cart con carrito vacío devuelve 200."""
        resp = client.get("/ecommerce/cart")
        assert resp.status_code == 200

    def test_checkout_page_loads(self, client, db_session, seed_basic_data):
        """GET /ecommerce/checkout devuelve 200."""
        resp = client.get("/ecommerce/checkout")
        assert resp.status_code == 200

    def test_search_page(self, client, db_session, seed_basic_data):
        """GET /ecommerce/search?q=silla devuelve 200."""
        resp = client.get("/ecommerce/search?q=silla")
        assert resp.status_code == 200

    def test_categories_page(self, client, db_session, seed_basic_data):
        """GET /ecommerce/categories devuelve 200."""
        resp = client.get("/ecommerce/categories")
        assert resp.status_code == 200

    def test_contact_page(self, client, db_session, seed_basic_data):
        """GET /ecommerce/contact devuelve 200."""
        resp = client.get("/ecommerce/contact")
        assert resp.status_code == 200

    def test_about_page(self, client, db_session, seed_basic_data):
        """GET /ecommerce/about devuelve 200."""
        resp = client.get("/ecommerce/about")
        assert resp.status_code == 200


class TestCartRoutes:
    """Tests de integración para rutas del carrito."""

    def test_add_to_cart_redirects(self, client, db_session, seed_basic_data):
        """POST cart/add redirige (302)."""
        product = seed_basic_data["product"]
        resp = client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )
        assert resp.status_code == 302

    def test_add_to_cart_updates_session(self, client, db_session, seed_basic_data):
        """Después de agregar, el carrito tiene items."""
        product = seed_basic_data["product"]
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 2},
        )
        resp = client.get("/ecommerce/cart")
        assert resp.status_code == 200
        # La página del carrito debería mostrar el producto
        assert b"Silla" in resp.data or b"silla" in resp.data

    def test_update_cart_item(self, client, db_session, seed_basic_data):
        """POST cart/update redirige."""
        product = seed_basic_data["product"]
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )
        resp = client.post(
            f"/ecommerce/cart/update/{product.id}",
            data={"quantity": 3},
        )
        assert resp.status_code == 302

    def test_remove_from_cart(self, client, db_session, seed_basic_data):
        """POST cart/remove redirige."""
        product = seed_basic_data["product"]
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )
        resp = client.post(f"/ecommerce/cart/remove/{product.id}")
        assert resp.status_code == 302

    def test_clear_cart(self, client, db_session, seed_basic_data):
        """POST cart/clear redirige."""
        product = seed_basic_data["product"]
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )
        resp = client.post("/ecommerce/cart/clear")
        assert resp.status_code == 302


class TestFreightQuoteAPI:
    """Tests para la API de cotización de flete."""

    def test_shipping_quote(self, client, db_session, seed_basic_data):
        """POST freight/quote retorna JSON válido."""
        resp = client.post(
            "/ecommerce/freight/quote",
            json={
                "delivery_mode": "shipping",
                "city": "Querétaro",
                "state": "Querétaro",
                "cart_total": "5000",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "cost" in data
        assert "total_with_freight" in data

    def test_pickup_quote(self, client, db_session, seed_basic_data):
        """POST freight/quote pickup retorna cost=$0."""
        resp = client.post(
            "/ecommerce/freight/quote",
            json={"delivery_mode": "pickup"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["cost"] == 0.0

    def test_invalid_delivery_mode(self, client, db_session, seed_basic_data):
        """POST freight/quote con modo inválido retorna 400."""
        resp = client.post(
            "/ecommerce/freight/quote",
            json={"delivery_mode": "teleportation"},
        )
        assert resp.status_code == 400

    def test_shipping_missing_city(self, client, db_session, seed_basic_data):
        """POST freight/quote shipping sin ciudad retorna 400."""
        resp = client.post(
            "/ecommerce/freight/quote",
            json={"delivery_mode": "shipping", "city": "", "state": ""},
        )
        assert resp.status_code == 400


class TestCPLookupAPI:
    """Tests para la API de búsqueda de código postal."""

    def test_invalid_cp(self, client, db_session, seed_basic_data):
        """GET api/cp/00000 retorna 404."""
        resp = client.get("/ecommerce/api/cp/00000")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"] is True


class TestCheckoutRoute:
    """Tests para el flujo de checkout vía HTTP."""

    def test_checkout_post_empty_cart(self, client, db_session, seed_basic_data):
        """POST checkout sin carrito retorna error."""
        pm = seed_basic_data["payment_method"]
        resp = client.post(
            "/ecommerce/checkout",
            data={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@test.com",
                "phone": "1234567890",
                "delivery_mode": "pickup",
                "payment_method_id": str(pm.id),
            },
        )
        # Debe retornar la misma página con error (400)
        assert resp.status_code == 400

    def test_checkout_post_validation_error(self, client, db_session, seed_basic_data):
        """POST checkout con datos inválidos retorna error."""
        product = seed_basic_data["product"]
        # Agregar producto al carrito
        client.post(
            f"/ecommerce/cart/add/{product.id}",
            data={"quantity": 1},
        )
        # Enviar checkout sin datos
        resp = client.post(
            "/ecommerce/checkout",
            data={
                "first_name": "",
                "last_name": "",
                "email": "",
                "phone": "",
            },
        )
        assert resp.status_code == 400
