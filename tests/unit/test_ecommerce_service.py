"""
Pruebas unitarias para EcommerceService.

Cubre: carrito (session), cálculos IVA, normalización,
filtrado/paginación, highlight, validaciones de checkout y freight.
"""

import pytest

from app.ecommerce.services import EcommerceService


class TestNormalizeQuantity:
    """Tests para _normalize_quantity."""

    def test_valid_int(self, app):
        assert EcommerceService._normalize_quantity(5) == 5

    def test_string_number(self, app):
        assert EcommerceService._normalize_quantity("3") == 3

    def test_negative_returns_minimum(self, app):
        assert EcommerceService._normalize_quantity(-1) == 1

    def test_zero_returns_minimum(self, app):
        assert EcommerceService._normalize_quantity(0) == 1

    def test_none_returns_minimum(self, app):
        assert EcommerceService._normalize_quantity(None) == 1

    def test_invalid_string_returns_minimum(self, app):
        assert EcommerceService._normalize_quantity("abc") == 1

    def test_custom_minimum(self, app):
        assert EcommerceService._normalize_quantity(0, minimum=5) == 5


class TestHighlightMatch:
    """Tests para _highlight_match."""

    def test_basic_highlight(self, app):
        result = EcommerceService._highlight_match("Silla Rústica", "silla")
        assert "<mark" in result
        assert "Silla" in result

    def test_no_match(self, app):
        result = EcommerceService._highlight_match("Mesa", "silla")
        assert "<mark" not in result
        assert "Mesa" in result

    def test_empty_search(self, app):
        result = EcommerceService._highlight_match("Test", "")
        assert result == "Test"

    def test_empty_value(self, app):
        result = EcommerceService._highlight_match("", "test")
        assert result == ""

    def test_html_escaping(self, app):
        result = EcommerceService._highlight_match(
            "<script>alert(1)</script>", "script"
        )
        assert "<script>" not in result
        assert "&lt;" in result


class TestToDecimal:
    """Tests para _to_decimal."""

    def test_valid_number(self, app):
        from decimal import Decimal

        result = EcommerceService._to_decimal("100.50")
        assert result == Decimal("100.50")

    def test_invalid_value(self, app):
        from decimal import Decimal

        result = EcommerceService._to_decimal("abc")
        assert result == Decimal("0")

    def test_none_value(self, app):
        from decimal import Decimal

        result = EcommerceService._to_decimal(None)
        assert result == Decimal("0")


class TestCartOperations:
    """Tests para operaciones del carrito de sesión."""

    def test_empty_cart(self, app, db_session, seed_basic_data):
        """Carrito vacío retorna estructura correcta."""
        with app.test_request_context():
            from flask import session

            session.clear()
            cart = EcommerceService.get_cart()
            assert cart["cart_items"] == []
            assert cart["subtotal"] == 0.0
            assert cart["iva"] == 0.0
            assert cart["total"] == 0.0
            assert cart["total_items"] == 0
            assert cart["iva_rate"] == 0.16

    def test_add_product_to_cart(self, app, db_session, seed_basic_data):
        """Agregar un producto al carrito."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            cart = EcommerceService.add_product_to_cart(
                product_id=product.id, quantity=2
            )
            assert cart["total_items"] == 2
            assert len(cart["cart_items"]) == 1

    def test_add_product_respects_stock_limit(self, app, db_session, seed_basic_data):
        """No agrega mas de lo que hay en stock."""
        product = seed_basic_data["product"]
        inventory = seed_basic_data["inventory"]  # stock=10

        with app.test_request_context():
            from flask import session

            session.clear()
            cart = EcommerceService.add_product_to_cart(
                product_id=product.id, quantity=999
            )
            assert cart["total_items"] == inventory.stock

    def test_add_nonexistent_product(self, app, db_session, seed_basic_data):
        """Agregar producto inexistente no modifica carrito."""
        with app.test_request_context():
            from flask import session

            session.clear()
            cart = EcommerceService.add_product_to_cart(product_id=99999, quantity=1)
            assert cart["total_items"] == 0

    def test_update_product_quantity(self, app, db_session, seed_basic_data):
        """Actualizar cantidad de producto en carrito."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=2)
            cart = EcommerceService.update_product_quantity(
                product_id=product.id, quantity=5
            )
            assert cart["total_items"] == 5

    def test_update_to_zero_removes_product(self, app, db_session, seed_basic_data):
        """Actualizar cantidad a 0 elimina el producto del carrito."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=2)
            cart = EcommerceService.update_product_quantity(
                product_id=product.id, quantity=0
            )
            assert cart["total_items"] == 0
            assert len(cart["cart_items"]) == 0

    def test_remove_product_from_cart(self, app, db_session, seed_basic_data):
        """Eliminar producto del carrito."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=2)
            cart = EcommerceService.remove_product_from_cart(product_id=product.id)
            assert cart["total_items"] == 0

    def test_clear_cart(self, app, db_session, seed_basic_data):
        """Vaciar carrito completo."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=3)
            cart = EcommerceService.clear_cart()
            assert cart["total_items"] == 0
            assert cart["cart_items"] == []

    def test_cart_iva_calculation(self, app, db_session, seed_basic_data):
        """Los cálculos de subtotal/IVA/total son correctos."""
        product = seed_basic_data["product"]  # price=1500
        with app.test_request_context():
            from flask import session

            session.clear()
            cart = EcommerceService.add_product_to_cart(
                product_id=product.id, quantity=1
            )
            assert cart["total"] > 0
            assert cart["iva"] > 0
            assert cart["subtotal"] > 0
            # total = subtotal + iva
            assert abs(cart["total"] - (cart["subtotal"] + cart["iva"])) < 0.02

    def test_add_custom_furniture_product_is_blocked(
        self, app, db_session, seed_basic_data
    ):
        """Los productos personalizados no se agregan al carrito e-commerce."""
        from app.models.furniture_type import FurnitureType
        from app.models.product import Product
        from app.models.product_inventory import ProductInventory

        custom_type = FurnitureType(
            title="Muebles personalizados test",
            subtitle="Categoria especial",
            image_url="https://example.com/custom.jpg",
            slug="muebles-personalizados-test",
            requires_contact_request=True,
            status=True,
        )
        db_session.add(custom_type)
        db_session.flush()

        custom_product = Product(
            sku="CUSTOM-TEST-001",
            name="Producto especial test",
            furniture_type_id=custom_type.id,
            description="Producto bajo pedido",
            price=2500.0,
            status=True,
        )
        db_session.add(custom_product)
        db_session.flush()

        db_session.add(
            ProductInventory(
                product_id=custom_product.id,
                stock=5,
            )
        )
        db_session.commit()

        with app.test_request_context():
            from flask import session

            session.clear()
            with pytest.raises(ValueError, match="bajo pedido"):
                EcommerceService.add_product_to_cart(
                    product_id=custom_product.id,
                    quantity=1,
                )


class TestFreightQuote:
    """Tests para cotización de flete."""

    def test_pickup_mode_zero_cost(self, app, db_session, seed_basic_data):
        """Modo pickup siempre cuesta $0."""
        from decimal import Decimal

        with app.test_request_context():
            quote = EcommerceService.quote_freight(
                delivery_mode="pickup",
                city="Querétaro",
                state="Querétaro",
                cart_total=Decimal("1000"),
            )
            assert quote["cost"] == 0.0
            assert quote["reason"] == "Recoleccion en tienda"


class TestCheckoutValidation:
    """Tests para validaciones del checkout."""

    def test_checkout_empty_cart_raises(self, app, db_session, seed_basic_data):
        """Carrito vacío lanza ValueError."""
        with app.test_request_context():
            from flask import session

            session.clear()
            with pytest.raises(ValueError, match="carrito esta vacio"):
                EcommerceService.checkout_from_form({})

    def test_checkout_missing_fields_raises(self, app, db_session, seed_basic_data):
        """Campos obligatorios faltantes lanzan ValueError."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=1)
            with pytest.raises(ValueError, match="obligatorios"):
                EcommerceService.checkout_from_form(
                    {"first_name": "Test", "last_name": "", "email": "", "phone": ""}
                )

    def test_checkout_invalid_email_raises(self, app, db_session, seed_basic_data):
        """Email inválido lanza ValueError."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=1)
            with pytest.raises(ValueError, match="correo electronico no es valido"):
                EcommerceService.checkout_from_form(
                    {
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "email": "not-an-email",
                        "phone": "4771234567",
                        "delivery_mode": "pickup",
                        "payment_method_id": str(seed_basic_data["payment_method"].id),
                    }
                )

    def test_checkout_invalid_delivery_mode_raises(
        self, app, db_session, seed_basic_data
    ):
        """Modo de entrega inválido lanza ValueError."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=1)
            with pytest.raises(ValueError, match="tipo de entrega"):
                EcommerceService.checkout_from_form(
                    {
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "email": "juan@test.com",
                        "phone": "4771234567",
                        "delivery_mode": "invalid",
                        "payment_method_id": "1",
                    }
                )

    def test_checkout_shipping_missing_zip(self, app, db_session, seed_basic_data):
        """Envío sin código postal lanza ValueError."""
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=1)
            with pytest.raises(ValueError, match="campos obligatorios de envio"):
                EcommerceService.checkout_from_form(
                    {
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "email": "juan2@test.com",
                        "phone": "4771234567",
                        "delivery_mode": "shipping",
                        "payment_method_id": str(pm.id),
                        "zip_code": "",
                        "state": "",
                        "city": "",
                        "street": "",
                        "neighborhood": "",
                        "exterior_number": "",
                    }
                )

    def test_checkout_invalid_zip_format(self, app, db_session, seed_basic_data):
        """CP con formato incorrecto lanza ValueError."""
        product = seed_basic_data["product"]
        pm = seed_basic_data["payment_method"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=1)
            with pytest.raises(ValueError, match="5 digitos"):
                EcommerceService.checkout_from_form(
                    {
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "email": "juan3@test.com",
                        "phone": "4771234567",
                        "delivery_mode": "shipping",
                        "payment_method_id": str(pm.id),
                        "zip_code": "123",
                        "state": "Querétaro",
                        "city": "Querétaro",
                        "street": "Calle 1",
                        "neighborhood": "Centro",
                        "exterior_number": "100",
                    }
                )

    def test_checkout_invalid_payment_method_raises(
        self, app, db_session, seed_basic_data
    ):
        """Método de pago inválido lanza ValueError."""
        product = seed_basic_data["product"]
        with app.test_request_context():
            from flask import session

            session.clear()
            EcommerceService.add_product_to_cart(product_id=product.id, quantity=1)
            with pytest.raises(ValueError, match="metodo de pago"):
                EcommerceService.checkout_from_form(
                    {
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "email": "juan4@test.com",
                        "phone": "4771234567",
                        "delivery_mode": "pickup",
                        "payment_method_id": "abc",
                    }
                )


class TestGetFilteredProducts:
    """Tests para get_filtered_products."""

    def test_default_returns_all(self, app, db_session, seed_basic_data):
        """Sin filtros retorna todos los productos activos."""
        with app.test_request_context():
            result = EcommerceService.get_filtered_products()
            assert "products" in result
            assert "total_products" in result
            assert "page" in result
            assert result["page"] == 1

    def test_search_filter(self, app, db_session, seed_basic_data):
        """Filtro por nombre funciona."""
        with app.test_request_context():
            result = EcommerceService.get_filtered_products(search_term="Rústica")
            assert result["filtered_total"] >= 1

    def test_search_no_results(self, app, db_session, seed_basic_data):
        """Búsqueda sin resultados retorna lista vacía."""
        with app.test_request_context():
            result = EcommerceService.get_filtered_products(
                search_term="producto_inexistente_xyz"
            )
            assert result["filtered_total"] == 0
            assert result["products"] == []

    def test_sort_by_price_asc(self, app, db_session, seed_basic_data):
        """Orden ascendente por precio."""
        with app.test_request_context():
            result = EcommerceService.get_filtered_products(sort_by="price_asc")
            prices = [p["price"] for p in result["products"]]
            assert prices == sorted(prices)

    def test_pagination_metadata(self, app, db_session, seed_basic_data):
        """Metadatos de paginación son correctos."""
        with app.test_request_context():
            result = EcommerceService.get_filtered_products(limit=1, page=1)
            assert result["total_pages"] >= 1
            assert result["limit"] == 1
