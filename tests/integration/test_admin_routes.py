"""
Pruebas de integración para rutas del panel admin.

Las rutas admin requieren autenticación. Se verifica que sin login
las rutas protegidas redirigen, y se prueba la API de POS.
"""


class TestAdminAuthProtection:
    """Verifica que las rutas admin requieren autenticación."""

    def test_admin_index_redirects(self, client, db_session, seed_basic_data):
        """GET /admin sin login redirige a login."""
        resp = client.get("/admin")
        assert resp.status_code in (302, 401)

    def test_pos_redirects(self, client, db_session, seed_basic_data):
        """GET /sales/pos sin login redirige."""
        resp = client.get("/sales/pos")
        assert resp.status_code in (302, 401)

    def test_customer_orders_redirects(self, client, db_session, seed_basic_data):
        """GET /customer-orders/ sin login redirige."""
        resp = client.get("/customer-orders/")
        assert resp.status_code in (302, 401)

    def test_products_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/products sin login redirige."""
        resp = client.get("/admin/products")
        assert resp.status_code in (302, 401, 308)

    def test_suppliers_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/suppliers sin login redirige."""
        resp = client.get("/admin/suppliers")
        assert resp.status_code in (302, 401, 308)

    def test_raw_materials_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/raw-materials sin login redirige."""
        resp = client.get("/admin/raw-materials")
        assert resp.status_code in (302, 401, 308)

    def test_production_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/production sin login redirige."""
        resp = client.get("/admin/production")
        assert resp.status_code in (302, 401, 308)

    def test_catalogs_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/catalogs sin login redirige."""
        resp = client.get("/admin/catalogs")
        assert resp.status_code in (302, 401, 308)

    def test_users_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/users sin login redirige."""
        resp = client.get("/admin/users")
        assert resp.status_code in (302, 401, 308)

    def test_reports_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/reports sin login redirige."""
        resp = client.get("/admin/reports")
        assert resp.status_code in (302, 401, 308)

    def test_costs_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/costs sin login redirige."""
        resp = client.get("/admin/costs")
        assert resp.status_code in (302, 401, 308)

    def test_purchases_admin_redirects(self, client, db_session, seed_basic_data):
        """GET /admin/purchases sin login redirige."""
        resp = client.get("/admin/purchases")
        assert resp.status_code in (302, 401, 308)


class TestPOSApiWithoutAuth:
    """Verifica que la API del POS requiere autenticación."""

    def test_pos_cart_api_redirects(self, client, db_session, seed_basic_data):
        """GET /sales/pos/cart sin login redirige."""
        resp = client.get("/sales/pos/cart")
        assert resp.status_code in (302, 401)

    def test_pos_add_item_redirects(self, client, db_session, seed_basic_data):
        """POST /sales/pos/items sin login redirige."""
        resp = client.post(
            "/sales/pos/items",
            json={"product_id": 1, "quantity": 1},
        )
        assert resp.status_code in (302, 401)

    def test_pos_checkout_redirects(self, client, db_session, seed_basic_data):
        """POST /sales/pos/checkout sin login redirige."""
        resp = client.post(
            "/sales/pos/checkout",
            json={"amount_given": 1000, "payment_method_id": 1},
        )
        assert resp.status_code in (302, 401)

    def test_pos_payment_methods_redirects(self, client, db_session, seed_basic_data):
        """GET /sales/pos/payment-methods sin login redirige."""
        resp = client.get("/sales/pos/payment-methods")
        assert resp.status_code in (302, 401)

    def test_pos_customers_search_redirects(self, client, db_session, seed_basic_data):
        """GET /sales/pos/customers?q=test sin login redirige."""
        resp = client.get("/sales/pos/customers?q=test")
        assert resp.status_code in (302, 401)

    def test_pos_create_customer_redirects(self, client, db_session, seed_basic_data):
        """POST /sales/pos/customers sin login redirige."""
        resp = client.post(
            "/sales/pos/customers",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "t@t.com",
                "phone": "123",
            },
        )
        assert resp.status_code in (302, 401)


class TestCustomerOrdersApiWithoutAuth:
    """Verifica que las rutas de órdenes de cliente requieren autenticación."""

    def test_orders_create_redirects(self, client, db_session, seed_basic_data):
        """POST /customer-orders/ sin login redirige."""
        resp = client.post(
            "/customer-orders/",
            json={
                "customer_id": 1,
                "items": [{"product_id": 1, "quantity": 1}],
                "estimated_delivery_date": "2026-04-15",
            },
        )
        assert resp.status_code in (302, 401)

    def test_orders_cancel_redirects(self, client, db_session, seed_basic_data):
        """POST /customer-orders/1/cancel sin login redirige."""
        resp = client.post(
            "/customer-orders/1/cancel",
            json={"reason": "test"},
        )
        assert resp.status_code in (302, 401, 404)

    def test_orders_status_update_redirects(self, client, db_session, seed_basic_data):
        """PUT /customer-orders/1/status sin login redirige."""
        resp = client.put(
            "/customer-orders/1/status",
            json={"status": "terminado"},
        )
        assert resp.status_code in (302, 401, 404)
