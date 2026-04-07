from types import SimpleNamespace

from app.rbac import (
    ROLE_ADMIN,
    ROLE_CLIENT,
    ROLE_PRODUCTION,
    ROLE_SALES,
    DASHBOARD_READ,
    USERS_READ,
    USERS_CREATE,
    SALES_CREATE,
    PRODUCTS_READ,
    AUDIT_READ,
    can,
    normalize_role_name,
    resolve_role_key,
    _resolve_endpoint_permissions,
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
    assert can(AUDIT_READ, user=user)
    assert not can(SALES_CREATE, user=user)


def test_notifications_endpoints_require_audit_read():
    assert _resolve_endpoint_permissions("notifications.index") == [AUDIT_READ]
    assert _resolve_endpoint_permissions("notifications.dismiss") == [AUDIT_READ]
    assert _resolve_endpoint_permissions("notifications.clear") == [AUDIT_READ]
    assert _resolve_endpoint_permissions("security_audit.details") == [AUDIT_READ]


def test_sales_role_has_sales_but_not_users_permissions():
    user = _user("Ventas")
    assert can(SALES_CREATE, user=user)
    assert not can(USERS_CREATE, user=user)
    assert not can(USERS_READ, user=user)
    assert not can(AUDIT_READ, user=user)


def test_unknown_or_unauthenticated_user_is_denied_by_default():
    unknown_role_user = _user("Gerente General")
    anonymous_user = _user("Administrador", authenticated=False)

    assert not can(PRODUCTS_READ, user=unknown_role_user)
    assert not can(PRODUCTS_READ, user=anonymous_user)


def test_dashboard_endpoint_requires_dashboard_read():
    assert _resolve_endpoint_permissions("index_admin") == [DASHBOARD_READ]
    assert _resolve_endpoint_permissions("dashboard.index") == [DASHBOARD_READ]


def test_dashboard_access_matches_documented_roles():
    assert can(DASHBOARD_READ, user=_user("Administrador"))
    assert can(DASHBOARD_READ, user=_user("Producción"))
    assert can(DASHBOARD_READ, user=_user("Ventas"))

    # Cliente no tiene acceso a dashboard interno según matriz RBAC.
    assert not can(DASHBOARD_READ, user=_user("Cliente"))
