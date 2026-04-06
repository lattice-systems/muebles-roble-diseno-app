"""Pruebas de integracion para seguridad de autenticacion."""

from __future__ import annotations

import uuid

from flask_security.recoverable import generate_reset_password_token
from flask_security.utils import hash_password

from app.models.role import Role
from app.models.user import User

TEST_PASSWORD = "PassTest#123"


def _create_admin_user(db_session) -> User:
    role = Role(name="Administrador", description="Administrador", status=True)
    db_session.add(role)
    db_session.flush()

    user = User(
        full_name="Usuario Admin Test",
        email="admin-security@test.com",
        password_hash=hash_password(TEST_PASSWORD),
        fs_uniquifier=uuid.uuid4().hex,
        role_id=role.id,
        status=True,
    )
    db_session.add(user)
    db_session.commit()

    return user


class TestPasswordRecoveryFlow:
    """Valida endpoints principales del flujo recoverable."""

    def test_forgot_password_page_is_available(self, client):
        response = client.get("/reset")

        assert response.status_code == 200
        assert "no-store" in response.headers.get("Cache-Control", "")

    def test_reset_password_form_renders_with_valid_token(self, client, db_session):
        user = _create_admin_user(db_session)
        token = generate_reset_password_token(user)

        response = client.get(f"/reset/{token}")

        assert response.status_code == 200
        assert b"Restablecer contrasena" in response.data


class TestLogoutHardening:
    """Valida limpieza de estado de sesion y cache al cerrar sesion."""

    def test_logout_clears_session_and_sets_secure_headers(self, client, db_session):
        user = _create_admin_user(db_session)

        with client.session_transaction() as session:
            session["_user_id"] = user.fs_uniquifier
            session["_fresh"] = True
            session["ecommerce_last_order_id"] = 999

        logout_response = client.post("/login/logout", follow_redirects=False)

        assert logout_response.status_code in (302, 303)
        assert "no-store" in logout_response.headers.get("Cache-Control", "")
        assert (
            logout_response.headers.get("Clear-Site-Data")
            == '"cache", "cookies", "storage"'
        )

        set_cookie_headers = logout_response.headers.getlist("Set-Cookie")
        assert any("session=;" in header for header in set_cookie_headers)
        assert any("remember_token=;" in header for header in set_cookie_headers)

        with client.session_transaction() as session:
            assert "_user_id" not in session
            assert "ecommerce_last_order_id" not in session
