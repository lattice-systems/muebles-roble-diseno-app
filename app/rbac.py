"""
Capa transversal de autorización RBAC.

Centraliza:
- Normalización de roles
- Matriz rol -> permisos
- Helpers `can()` / `can_any()` para backend y templates
- Decoradores reutilizables por permiso fijo/dinámico
- Enforzamiento global (deny-by-default) para rutas internas
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any

from flask import current_app, jsonify, redirect, request
from flask_security import current_user, url_for_security

from app.exceptions import ForbiddenError
from app.extensions import db
from app.shared.security_logging import log_security_event

# ---------------------------------------------------------------------------
# Roles canónicos
# ---------------------------------------------------------------------------

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_PRODUCTION = "production"
ROLE_SALES = "sales"
ROLE_CLIENT = "client"

CANONICAL_ROLES = {
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
    ROLE_PRODUCTION,
    ROLE_SALES,
    ROLE_CLIENT,
}

ROLE_ALIASES = {
    "superadmin": ROLE_SUPERADMIN,
    "super admin": ROLE_SUPERADMIN,
    "super-admin": ROLE_SUPERADMIN,
    "super administrador": ROLE_SUPERADMIN,
    "súper administrador": ROLE_SUPERADMIN,
    "admin": ROLE_ADMIN,
    "administrador": ROLE_ADMIN,
    "production": ROLE_PRODUCTION,
    "produccion": ROLE_PRODUCTION,
    "sales": ROLE_SALES,
    "ventas": ROLE_SALES,
    "client": ROLE_CLIENT,
    "cliente": ROLE_CLIENT,
}


# ---------------------------------------------------------------------------
# Permisos (convención estable: modulo.accion)
# ---------------------------------------------------------------------------

INTERNAL_ACCESS = "internal.access"

DASHBOARD_READ = "dashboard.read"

USERS_READ = "users.read"
USERS_CREATE = "users.create"
USERS_UPDATE = "users.update"
USERS_DELETE = "users.delete"
USERS_EXPORT = "users.export"
USERS_MANAGE = "users.manage"

CATALOGS_READ = "catalogs.read"
CATALOGS_CREATE = "catalogs.create"
CATALOGS_UPDATE = "catalogs.update"
CATALOGS_DELETE = "catalogs.delete"
CATALOGS_EXPORT = "catalogs.export"

SUPPLIERS_READ = "suppliers.read"
SUPPLIERS_CREATE = "suppliers.create"
SUPPLIERS_UPDATE = "suppliers.update"
SUPPLIERS_DELETE = "suppliers.delete"
SUPPLIERS_EXPORT = "suppliers.export"

PURCHASES_READ = "purchases.read"
PURCHASES_CREATE = "purchases.create"
PURCHASES_UPDATE = "purchases.update"
PURCHASES_DELETE = "purchases.delete"
PURCHASES_EXPORT = "purchases.export"

RAW_MATERIALS_READ = "raw_materials.read"
RAW_MATERIALS_CREATE = "raw_materials.create"
RAW_MATERIALS_UPDATE = "raw_materials.update"
RAW_MATERIALS_DELETE = "raw_materials.delete"
RAW_MATERIALS_EXPORT = "raw_materials.export"

PRODUCTION_READ = "production.read"
PRODUCTION_CREATE = "production.create"
PRODUCTION_UPDATE = "production.update"
PRODUCTION_DELETE = "production.delete"

PRODUCTS_READ = "products.read"
PRODUCTS_CREATE = "products.create"
PRODUCTS_UPDATE = "products.update"
PRODUCTS_DELETE = "products.delete"
PRODUCTS_EXPORT = "products.export"

SALES_READ = "sales.read"
SALES_CREATE = "sales.create"
SALES_UPDATE = "sales.update"

CUSTOMER_ORDERS_READ = "customer_orders.read"
CUSTOMER_ORDERS_CREATE = "customer_orders.create"
CUSTOMER_ORDERS_UPDATE = "customer_orders.update"

CONTACT_REQUESTS_READ = "contact_requests.read"
CONTACT_REQUESTS_MANAGE = "contact_requests.manage"

COSTS_READ = "costs.read"
COSTS_CREATE = "costs.create"
COSTS_UPDATE = "costs.update"
COSTS_DELETE = "costs.delete"
COSTS_EXPORT = "costs.export"

REPORTS_READ = "reports.read"
REPORTS_EXPORT = "reports.export"
REPORTS_REFRESH = "reports.refresh"

ECOMMERCE_MANAGE = "ecommerce.manage"
AUDIT_READ = "audit.read"

ALL_PERMISSIONS = {
    INTERNAL_ACCESS,
    DASHBOARD_READ,
    USERS_READ,
    USERS_CREATE,
    USERS_UPDATE,
    USERS_DELETE,
    USERS_EXPORT,
    USERS_MANAGE,
    CATALOGS_READ,
    CATALOGS_CREATE,
    CATALOGS_UPDATE,
    CATALOGS_DELETE,
    CATALOGS_EXPORT,
    SUPPLIERS_READ,
    SUPPLIERS_CREATE,
    SUPPLIERS_UPDATE,
    SUPPLIERS_DELETE,
    SUPPLIERS_EXPORT,
    PURCHASES_READ,
    PURCHASES_CREATE,
    PURCHASES_UPDATE,
    PURCHASES_DELETE,
    PURCHASES_EXPORT,
    RAW_MATERIALS_READ,
    RAW_MATERIALS_CREATE,
    RAW_MATERIALS_UPDATE,
    RAW_MATERIALS_DELETE,
    RAW_MATERIALS_EXPORT,
    PRODUCTION_READ,
    PRODUCTION_CREATE,
    PRODUCTION_UPDATE,
    PRODUCTION_DELETE,
    PRODUCTS_READ,
    PRODUCTS_CREATE,
    PRODUCTS_UPDATE,
    PRODUCTS_DELETE,
    PRODUCTS_EXPORT,
    SALES_READ,
    SALES_CREATE,
    SALES_UPDATE,
    CUSTOMER_ORDERS_READ,
    CUSTOMER_ORDERS_CREATE,
    CUSTOMER_ORDERS_UPDATE,
    CONTACT_REQUESTS_READ,
    CONTACT_REQUESTS_MANAGE,
    COSTS_READ,
    COSTS_CREATE,
    COSTS_UPDATE,
    COSTS_DELETE,
    COSTS_EXPORT,
    REPORTS_READ,
    REPORTS_EXPORT,
    REPORTS_REFRESH,
    ECOMMERCE_MANAGE,
    AUDIT_READ,
}


ADMIN_RESTRICTED_PERMISSIONS = {
    SALES_CREATE,
    SALES_UPDATE,
    CUSTOMER_ORDERS_CREATE,
    CUSTOMER_ORDERS_UPDATE,
}

ADMIN_PERMISSIONS = set(ALL_PERMISSIONS) - ADMIN_RESTRICTED_PERMISSIONS

# Matriz operativa objetivo
ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_SUPERADMIN: set(ALL_PERMISSIONS),
    ROLE_ADMIN: set(ADMIN_PERMISSIONS),
    ROLE_PRODUCTION: {
        INTERNAL_ACCESS,
        DASHBOARD_READ,
        CATALOGS_READ,
        CATALOGS_EXPORT,
        SUPPLIERS_READ,
        SUPPLIERS_EXPORT,
        PURCHASES_READ,
        PURCHASES_EXPORT,
        RAW_MATERIALS_CREATE,
        RAW_MATERIALS_READ,
        RAW_MATERIALS_UPDATE,
        RAW_MATERIALS_EXPORT,
        PRODUCTION_CREATE,
        PRODUCTION_READ,
        PRODUCTION_UPDATE,
        PRODUCTS_CREATE,
        PRODUCTS_READ,
        PRODUCTS_UPDATE,
        PRODUCTS_EXPORT,
        COSTS_READ,
        COSTS_EXPORT,
        REPORTS_READ,
    },
    ROLE_SALES: {
        INTERNAL_ACCESS,
        DASHBOARD_READ,
        CATALOGS_READ,
        CATALOGS_EXPORT,
        RAW_MATERIALS_READ,
        RAW_MATERIALS_EXPORT,
        PRODUCTION_READ,
        PRODUCTS_READ,
        PRODUCTS_EXPORT,
        SALES_CREATE,
        SALES_READ,
        SALES_UPDATE,
        CUSTOMER_ORDERS_CREATE,
        CUSTOMER_ORDERS_READ,
        CUSTOMER_ORDERS_UPDATE,
        CONTACT_REQUESTS_READ,
        CONTACT_REQUESTS_MANAGE,
        COSTS_READ,
        COSTS_EXPORT,
        REPORTS_READ,
    },
    ROLE_CLIENT: {
        PRODUCTS_READ,
    },
}


# ---------------------------------------------------------------------------
# Normalización y checks de rol/permiso
# ---------------------------------------------------------------------------


def normalize_role_name(value: str | None) -> str:
    """Normaliza nombre de rol (insensible a mayúsculas/acentos/espacios)."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().strip().split())


def resolve_role_key(role_name: str | None) -> str | None:
    normalized = normalize_role_name(role_name)
    if not normalized:
        return None
    return ROLE_ALIASES.get(normalized)


def get_user_role_key(user: Any | None = None) -> str | None:
    target_user = user or current_user
    if not getattr(target_user, "is_authenticated", False):
        return None
    role = getattr(target_user, "role", None)
    role_name = getattr(role, "name", None) if role is not None else None
    return resolve_role_key(role_name)


def get_role_permissions(role_key: str | None) -> set[str]:
    if not role_key:
        return set()
    return set(ROLE_PERMISSIONS.get(role_key, set()))


def can(permission: str, user: Any | None = None) -> bool:
    """Retorna True si el usuario tiene un permiso concreto."""
    if not permission:
        return False
    role_key = get_user_role_key(user)
    if not role_key:
        return False
    return permission in get_role_permissions(role_key)


def can_any(*permissions: str, user: Any | None = None) -> bool:
    """Retorna True si el usuario tiene al menos un permiso de la lista."""
    if not permissions:
        return False
    return any(can(permission, user=user) for permission in permissions if permission)


# ---------------------------------------------------------------------------
# Respuesta de seguridad y decoradores reutilizables
# ---------------------------------------------------------------------------

JSON_PERMISSION_ENDPOINTS = {
    # Sales API
    "sales.search_customers",
    "sales.create_customer",
    "sales.get_customer",
    "sales.update_customer_data",
    "sales.get_cart",
    "sales.add_item",
    "sales.update_item",
    "sales.remove_item",
    "sales.clear_cart",
    "sales.checkout",
    "sales.get_payment_methods",
    "sales.lookup_cp",
    # Customer orders API-like endpoints
    "customer_orders.create",
    "customer_orders.cancel",
    "customer_orders.send_to_production",
    "customer_orders.update_status",
    "customer_orders.search_customers",
    "customer_orders.search_products_api",
}


def _wants_json_forbidden(endpoint: str | None = None) -> bool:
    if endpoint in JSON_PERMISSION_ENDPOINTS:
        return True

    if request.is_json:
        return True

    xrw = (request.headers.get("X-Requested-With") or "").strip().lower()
    if xrw == "xmlhttprequest":
        return True

    best = request.accept_mimetypes.best
    if best == "application/json":
        return True

    if (
        request.accept_mimetypes.accept_json
        and not request.accept_mimetypes.accept_html
    ):
        return True

    return False


def _unauthorized_response():
    _log_security_access_event(
        event_type="auth.unauthenticated.access",
        result="denied",
        reason="Intento de acceso sin sesion autenticada",
        endpoint=request.endpoint,
    )
    login_url = url_for_security("login", next=request.url)
    return redirect(login_url)


def _forbidden_response(
    message: str = "No tienes permisos para realizar esta acción.",
    endpoint: str | None = None,
):
    _log_security_access_event(
        event_type="auth.rbac.denied",
        result="denied",
        reason=message,
        endpoint=endpoint,
    )
    if _wants_json_forbidden(endpoint=endpoint):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 403,
                        "message": message,
                    },
                }
            ),
            403,
        )
    raise ForbiddenError(message)


def _log_security_access_event(
    *,
    event_type: str,
    result: str,
    reason: str,
    endpoint: str | None,
) -> None:
    try:
        user_id = None
        email = None
        if getattr(current_user, "is_authenticated", False):
            user_id = getattr(current_user, "id", None)
            email = getattr(current_user, "email", None)

        log_security_event(
            event_type=event_type,
            result=result,
            user_id=user_id,
            email_or_identifier=email,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.headers.get("User-Agent"),
            reason=reason,
            context_data={
                "path": request.path,
                "method": request.method,
                "endpoint": endpoint,
            },
            source="rbac_guard",
            commit=True,
        )
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("No se pudo registrar evento RBAC: %s", exc)


def _normalize_required_permissions(required: Any) -> list[str]:
    if required is None:
        return []
    if isinstance(required, str):
        return [required]
    if isinstance(required, Iterable):
        return [str(item) for item in required if item]
    return [str(required)]


def require_permission(permission: str):
    """Decorator reusable para rutas con permiso fijo."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not getattr(current_user, "is_authenticated", False):
                return _unauthorized_response()
            if not can(permission):
                return _forbidden_response(endpoint=request.endpoint)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_dynamic_permission(resolver_fn: Callable[[], str | Iterable[str] | None]):
    """Decorator reusable para rutas con permiso dinámico (ej. bulk action)."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not getattr(current_user, "is_authenticated", False):
                return _unauthorized_response()

            required = _normalize_required_permissions(resolver_fn())
            if not required:
                return _forbidden_response(endpoint=request.endpoint)

            if not can_any(*required):
                return _forbidden_response(endpoint=request.endpoint)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def resolve_action_permission(action_map: dict[str, str], action_key: str = "action"):
    """
    Resuelve permiso por acción enviada en form/json/query.

    action_map ejemplo:
    {
        "export": "users.export",
        "activate": "users.delete",
        "deactivate": "users.delete",
    }
    """
    json_data = request.get_json(silent=True) or {}
    raw_action = (
        request.form.get(action_key)
        or request.args.get(action_key)
        or json_data.get(action_key)
        or ""
    )
    action = str(raw_action).strip().lower()
    return action_map.get(action)


# ---------------------------------------------------------------------------
# Enforzamiento global (deny-by-default)
# ---------------------------------------------------------------------------

INTERNAL_PREFIXES = ("/admin",)

EndpointPermission = str | Iterable[str] | Callable[[], str | Iterable[str] | None]


def _build_endpoint_permission_map() -> dict[str, EndpointPermission]:
    endpoint_permissions: dict[str, EndpointPermission] = {
        # Dashboard / accesos raíz admin
        "index_admin": DASHBOARD_READ,
        "dashboard.index": DASHBOARD_READ,
        "catalogs_index": CATALOGS_READ,
        # Users
        "users.index": USERS_READ,
        "users.create_user": USERS_CREATE,
        "users.edit_user": USERS_UPDATE,
        "users.detail_user": USERS_READ,
        "users.toggle_status": (USERS_DELETE, USERS_UPDATE),
        "users.toggle_customer_status": (USERS_DELETE, USERS_UPDATE),
        "users.bulk_action_users": lambda: resolve_action_permission(
            {
                "export": USERS_EXPORT,
                "activate": USERS_DELETE,
                "deactivate": USERS_DELETE,
            }
        ),
        "users.profile": INTERNAL_ACCESS,
        "users.setup_2fa": INTERNAL_ACCESS,
        # Roles (solo admin, dentro de auth/users)
        "roles.list_roles": USERS_MANAGE,
        "roles.create_role": USERS_MANAGE,
        "roles.edit_role": USERS_MANAGE,
        "roles.delete_role": USERS_MANAGE,
        # Catálogos
        "colors.list_colors": CATALOGS_READ,
        "colors.create_color": CATALOGS_CREATE,
        "colors.edit_color": CATALOGS_UPDATE,
        "colors.delete_color": CATALOGS_DELETE,
        "colors.bulk_activate": CATALOGS_DELETE,
        "colors.bulk_deactivate": CATALOGS_DELETE,
        "colors.bulk_export": CATALOGS_EXPORT,
        "furniture_type.list_furniture_type": CATALOGS_READ,
        "furniture_type.create_furniture_type": CATALOGS_CREATE,
        "furniture_type.edit_furniture_type": CATALOGS_UPDATE,
        "furniture_type.delete_furniture_type": CATALOGS_DELETE,
        "furniture_type.bulk_activate": CATALOGS_DELETE,
        "furniture_type.bulk_deactivate": CATALOGS_DELETE,
        "furniture_type.bulk_export": CATALOGS_EXPORT,
        "payment_method.list_payment_method": CATALOGS_READ,
        "payment_method.create_payment_method": CATALOGS_CREATE,
        "payment_method.edit_payment_method": CATALOGS_UPDATE,
        "payment_method.delete_payment_method": CATALOGS_DELETE,
        "payment_method.bulk_activate": CATALOGS_DELETE,
        "payment_method.bulk_deactivate": CATALOGS_DELETE,
        "payment_method.bulk_export": CATALOGS_EXPORT,
        "unit_of_measures.list_unit_of_measures": CATALOGS_READ,
        "unit_of_measures.create_unit_of_measure": CATALOGS_CREATE,
        "unit_of_measures.edit_unit_of_measure": CATALOGS_UPDATE,
        "unit_of_measures.delete_unit_of_measure": CATALOGS_DELETE,
        "unit_of_measures.bulk_activate_unit_of_measures": CATALOGS_DELETE,
        "unit_of_measures.bulk_deactivate_unit_of_measures": CATALOGS_DELETE,
        "unit_of_measures.bulk_export": CATALOGS_EXPORT,
        "woods_types.list_wood_types": CATALOGS_READ,
        "woods_types.create_wood_type": CATALOGS_CREATE,
        "woods_types.edit_wood_type": CATALOGS_UPDATE,
        "woods_types.delete_wood_type": CATALOGS_DELETE,
        "woods_types.bulk_activate": CATALOGS_DELETE,
        "woods_types.bulk_deactivate": CATALOGS_DELETE,
        "woods_types.bulk_export": CATALOGS_EXPORT,
        # Suppliers
        "suppliers.index": SUPPLIERS_READ,
        "suppliers.detail_supplier": SUPPLIERS_READ,
        "suppliers.create_supplier": SUPPLIERS_CREATE,
        "suppliers.edit_supplier": SUPPLIERS_UPDATE,
        "suppliers.toggle_status": SUPPLIERS_DELETE,
        "suppliers.bulk_action_suppliers": lambda: resolve_action_permission(
            {
                "export": SUPPLIERS_EXPORT,
                "activate": SUPPLIERS_DELETE,
                "deactivate": SUPPLIERS_DELETE,
            }
        ),
        # Purchases
        "purchases.index": PURCHASES_READ,
        "purchases.detail_order": PURCHASES_READ,
        "purchases.create_order": PURCHASES_CREATE,
        "purchases.edit_order": PURCHASES_UPDATE,
        "purchases.change_status_order": PURCHASES_UPDATE,
        "purchases.delete_order": PURCHASES_DELETE,
        "purchases.bulk_action_orders": lambda: resolve_action_permission(
            {"export": PURCHASES_EXPORT}
        ),
        # Raw materials
        "raw_materials.index": RAW_MATERIALS_READ,
        "raw_materials.detail_raw_material": RAW_MATERIALS_READ,
        "raw_materials.create_raw_material": RAW_MATERIALS_CREATE,
        "raw_materials.edit_raw_material": RAW_MATERIALS_UPDATE,
        "raw_materials.adjust_stock": RAW_MATERIALS_UPDATE,
        "raw_materials.toggle_status": RAW_MATERIALS_DELETE,
        "raw_materials.bulk_action_raw_materials": lambda: resolve_action_permission(
            {
                "export": RAW_MATERIALS_EXPORT,
                "activate": RAW_MATERIALS_DELETE,
                "deactivate": RAW_MATERIALS_DELETE,
            }
        ),
        # Production + BOM
        "production.orders_index": PRODUCTION_READ,
        "production.order_details": PRODUCTION_READ,
        "production.create_order": PRODUCTION_CREATE,
        "production.update_order_status": PRODUCTION_UPDATE,
        "production.assign_order": PRODUCTION_UPDATE,
        "production.update_order_materials": PRODUCTION_UPDATE,
        "production.initialize_order_materials": PRODUCTION_UPDATE,
        "production.boms_index": PRODUCTION_READ,
        "production.bom_details": PRODUCTION_READ,
        "production.create_bom": PRODUCTION_CREATE,
        "production.edit_bom": PRODUCTION_UPDATE,
        # Products
        "products.index": PRODUCTS_READ,
        "products.details": PRODUCTS_READ,
        "products.create": PRODUCTS_CREATE,
        "products.edit": PRODUCTS_UPDATE,
        "products.delete_image": PRODUCTS_UPDATE,
        "products.change_status": PRODUCTS_DELETE,
        "products.bulk_action_products": lambda: resolve_action_permission(
            {
                "export": PRODUCTS_EXPORT,
                "activate": PRODUCTS_DELETE,
                "deactivate": PRODUCTS_DELETE,
            }
        ),
        # Costs
        "costs.index": COSTS_READ,
        "costs.details": COSTS_READ,
        "costs.export_cost_csv": COSTS_EXPORT,
        "costs.export_list_csv": COSTS_EXPORT,
        "costs.bulk_action_costs": lambda: resolve_action_permission(
            {
                "export": COSTS_EXPORT,
            }
        ),
        # Reports + dashboard
        "reports.index": REPORTS_READ,
        "reports.sales_details": REPORTS_READ,
        "reports.top_products_details": REPORTS_READ,
        "reports.raw_material_consumption_details": REPORTS_READ,
        "reports.general_report_details": REPORTS_READ,
        "reports.export_daily_cut_csv": REPORTS_EXPORT,
        "reports.export_recent_sale": REPORTS_EXPORT,
        "reports.bulk_action_reports": lambda: resolve_action_permission(
            {
                "export": REPORTS_EXPORT,
            }
        ),
        "reports.refresh": REPORTS_REFRESH,
        # Audit
        "audit.index": AUDIT_READ,
        "audit.details": AUDIT_READ,
        "security_audit.index": AUDIT_READ,
        "security_audit.details": AUDIT_READ,
        "notifications.index": AUDIT_READ,
        "notifications.dismiss": AUDIT_READ,
        "notifications.clear": AUDIT_READ,
        # Sales POS
        "sales.pos": SALES_READ,
        "sales.ticket": SALES_READ,
        "sales.search_customers": SALES_READ,
        "sales.get_customer": SALES_READ,
        "sales.get_cart": SALES_READ,
        "sales.get_payment_methods": SALES_READ,
        "sales.lookup_cp": SALES_READ,
        "sales.open_sale": SALES_CREATE,
        "sales.create_customer": SALES_CREATE,
        "sales.add_item": SALES_CREATE,
        "sales.checkout": SALES_CREATE,
        "sales.update_customer_data": SALES_UPDATE,
        "sales.update_item": SALES_UPDATE,
        "sales.remove_item": SALES_UPDATE,
        "sales.clear_cart": SALES_UPDATE,
        # Customer Orders
        "customer_orders.index": CUSTOMER_ORDERS_READ,
        "customer_orders.detail": CUSTOMER_ORDERS_READ,
        "customer_orders.search_customers": CUSTOMER_ORDERS_READ,
        "customer_orders.search_products_api": CUSTOMER_ORDERS_READ,
        "customer_orders.create": CUSTOMER_ORDERS_CREATE,
        "customer_orders.cancel": CUSTOMER_ORDERS_UPDATE,
        "customer_orders.send_to_production": CUSTOMER_ORDERS_UPDATE,
        "customer_orders.update_status": CUSTOMER_ORDERS_UPDATE,
        # Contact Requests
        "contact_requests.index": CONTACT_REQUESTS_READ,
        "contact_requests.detail": CONTACT_REQUESTS_READ,
        "contact_requests.assign_to_me": CONTACT_REQUESTS_MANAGE,
        "contact_requests.update_status": CONTACT_REQUESTS_MANAGE,
        "contact_requests.convert_to_special_order": CONTACT_REQUESTS_MANAGE,
    }
    return endpoint_permissions


ENDPOINT_PERMISSION_MAP = _build_endpoint_permission_map()


def _resolve_endpoint_permissions(endpoint: str) -> list[str]:
    required = ENDPOINT_PERMISSION_MAP.get(endpoint)
    if callable(required):
        required = required()
    return _normalize_required_permissions(required)


def enforce_request_rbac():
    """Guard global RBAC para rutas internas (deny-by-default)."""
    path = request.path or ""
    if not path.startswith(INTERNAL_PREFIXES):
        return None

    endpoint = request.endpoint
    if not endpoint:
        return None

    if not getattr(current_user, "is_authenticated", False):
        return _unauthorized_response()

    required_permissions = _resolve_endpoint_permissions(endpoint)
    if not required_permissions:
        current_app.logger.warning(
            "RBAC deny-by-default: endpoint interno sin política explícita: %s",
            endpoint,
        )
        return _forbidden_response(
            message="No existe una política de acceso definida para este endpoint.",
            endpoint=endpoint,
        )

    if not can_any(*required_permissions):
        return _forbidden_response(endpoint=endpoint)

    return None


def register_rbac(app):
    """Registra RBAC global y helpers para Jinja."""

    @app.before_request
    def _rbac_before_request():
        return enforce_request_rbac()

    app.jinja_env.globals["can"] = can
    app.jinja_env.globals["can_any"] = can_any
