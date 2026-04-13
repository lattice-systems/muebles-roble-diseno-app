"""Pruebas de integración para rutas de contact requests."""

from __future__ import annotations

from datetime import date, timedelta

from app.models.contact_request import ContactRequest


def _login_admin_session(client, user) -> None:
    with client.session_transaction() as session:
        session["_user_id"] = user.fs_uniquifier
        session["_fresh"] = True


class TestContactRequestConversionRoute:
    """Valida conversión de solicitud a orden especial vía endpoint admin."""

    def test_convert_route_creates_order_and_redirects(
        self, client, app, db_session, seed_basic_data
    ):
        user = seed_basic_data["user"]
        _login_admin_session(client, user)

        contact_request = ContactRequest(
            full_name="Mario Herrera",
            email="mario.herrera@test.com",
            phone="4776661122",
            subject="Mesa de centro personalizada",
            message="Busco una mesa de centro con medidas específicas.",
            request_type="custom_furniture",
            status="new",
            source="ecommerce",
        )
        db_session.add(contact_request)
        db_session.commit()

        response = client.post(
            f"/admin/contact-requests/{contact_request.id}/convert",
            data={
                "product_name": "Mesa de centro a medida",
                "quantity": "1",
                "unit_price": "2890.00",
                "estimated_delivery_date": (
                    date.today() + timedelta(days=14)
                ).isoformat(),
                "phone": "4776661122",
                "notes": "Tono nogal oscuro.",
            },
            follow_redirects=False,
        )

        assert response.status_code in (302, 303)
        assert "/admin/customer-orders/" in (response.headers.get("Location") or "")

        with app.app_context():
            refreshed = db_session.get(ContactRequest, contact_request.id)
            assert refreshed is not None
            assert refreshed.converted_order_id is not None
            assert refreshed.status == "completed"
