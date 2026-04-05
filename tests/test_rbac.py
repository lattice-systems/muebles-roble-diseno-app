from types import SimpleNamespace

from app.rbac import (
    ROLE_ADMIN,
    ROLE_PRODUCTION,
    ROLE_SALES,
    USERS_READ,
    USERS_CREATE,
    SALES_CREATE,
    PRODUCTS_READ,
    can,
    normalize_role_name,
    resolve_role_key,
)


def _user(role_name: str, authenticated: bool = True):
    return SimpleNamespace(
        is_authenticated=authenticated,
        role=SimpleNamespace(name=role_name),
    )


def test_normalize_role_name_is_accent_case_and_space_insensitive():
    assert normalize_role_name("  PRODUCCIÓN ") == "produccion"
    assert normalize_role_name("Administrador") == "administrador"
    assert normalize_role_name("  Ventas  ") == "ventas"


def test_resolve_role_key_maps_canonical_aliases():
    assert resolve_role_key("Administrador") == ROLE_ADMIN
    assert resolve_role_key("PRODUCCIÓN") == ROLE_PRODUCTION
    assert resolve_role_key("ventas") == ROLE_SALES
    assert resolve_role_key("desconocido") is None


def test_admin_has_broad_permissions():
    user = _user("Administrador")
    assert can(USERS_READ, user=user)
    assert can(USERS_CREATE, user=user)
    assert not can(SALES_CREATE, user=user)


def test_sales_role_has_sales_but_not_users_permissions():
    user = _user("Ventas")
    assert can(SALES_CREATE, user=user)
    assert not can(USERS_CREATE, user=user)
    assert not can(USERS_READ, user=user)


def test_unknown_or_unauthenticated_user_is_denied_by_default():
    unknown_role_user = _user("Gerente General")
    anonymous_user = _user("Administrador", authenticated=False)

    assert not can(PRODUCTS_READ, user=unknown_role_user)
    assert not can(PRODUCTS_READ, user=anonymous_user)
