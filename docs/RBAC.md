# RBAC (Role Based Access Control)

Este proyecto implementa una capa RBAC transversal con política `deny-by-default`.

## Roles canónicos

- `Administrador`
- `Producción`
- `Ventas`
- `Cliente` (reservado para futuras capacidades con cuenta)

## Convención de permisos

Formato estable: `modulo.accion`

Ejemplos:

- `users.read`
- `catalogs.export`
- `raw_materials.update`
- `reports.refresh`

## APIs reutilizables

Definidas en `app/rbac.py`:

- `require_permission("modulo.accion")`
- `require_dynamic_permission(resolver_fn)`
- `can("modulo.accion")`
- `can_any("perm.a", "perm.b")`

## Enforzamiento global

`register_rbac(app)` registra un `before_request` que:

1. Aplica RBAC en rutas internas (`/admin`, `/sales`, `/customer-orders`)
2. Exige autenticación
3. Evalúa permisos por endpoint
4. Deniega por defecto endpoints internos sin política explícita

## UI

Los templates pueden ocultar enlaces/acciones con:

```jinja2
{% if can('reports.read') %}
  ...
{% endif %}
```

## Migración de roles base

La migración `3f9a8d2c7b11_ensure_canonical_rbac_roles.py` asegura de forma idempotente la existencia de:

- Administrador
- Producción
- Ventas
- Cliente

