# RBAC (Role Based Access Control)

Este proyecto implementa una capa RBAC transversal con política `deny-by-default`.

## Fuente de verdad funcional

Validación realizada contra el documento:

- `Usuarios-Roble-diseño.pdf`
- Sección `3.4 Requisitos de Control de Acceso`
- Sub-sección `3.4.2 Matriz de permisos por módulo`
- Fecha y versión del documento: `26/02/2026`, `v1.0`

Conclusión de validación:

- Los roles esenciales del sistema son **4** y se mantienen como canónicos:
  - `Administrador`
  - `Producción`
  - `Ventas`
  - `Cliente`
- **No se requieren roles adicionales** en la fase actual.

## Convención de permisos en código

Formato estable: `modulo.accion`

Ejemplos:

- `users.read`
- `catalogs.export`
- `raw_materials.update`
- `reports.refresh`

## Matriz validada (PDF vs implementación)

Leyenda PDF:

- `C,R,U,D`: CRUD
- `L`: solo lectura
- `CT`: consulta total
- `CP`: consulta parcial
- `ADM`: administración
- `UC`: uso completo usuario final

| Módulo | PDF 3.4.2 | Implementado en `app/rbac.py` | Estado |
|---|---|---|---|
| Autenticación y Usuarios | Admin: `C,R,U,D`; Cliente: `UC` | Admin: `users.*`; Internos: `profile/2FA/logout` por `internal.access`; Cliente sin sesión en esta fase | Alineado con ajuste de alcance |
| Catálogos | Admin: `C,R,U,D`; Prod: `L`; Ventas: `L` | Admin: `catalogs.create/read/update/delete/export`; Prod/Ventas: `catalogs.read/export` | Alineado + extra `export` |
| Proveedores y Compras | Admin: `C,R,U,D`; Prod: `L` | Admin: `suppliers.*`, `purchases.*`; Prod: `read/export` | Alineado + extra `export` |
| Inventario Materia Prima | Admin: `C,R,U,D`; Prod: `C,R,U`; Ventas: `L` | Admin: `raw_materials.*`; Prod: `create/read/update/export`; Ventas: `read/export` | Alineado + extra `export` |
| Recetas (BOM) | Admin: `C,R,U,D`; Prod: `C,R,U`; Ventas: `L` | Módulo `production` con permisos `read/create/update/delete` por rol | Alineado |
| Producción | Admin: `C,R,U,D`; Prod: `C,R,U`; Ventas: `L` | `production.read/create/update/delete` según rol | Alineado |
| Productos Terminados | Admin: `C,R,U,D`; Prod: `C,R,U`; Ventas: `L`; Cliente: `L` | Admin: `products.*`; Prod: `create/read/update/export`; Ventas: `read/export`; Cliente: `products.read` | Alineado + extra `export` |
| Ventas Físicas y Órdenes | Ventas: `C,R,U`; Admin: `R` | `sales` y `customer_orders`: Ventas `create/read/update`; Admin solo lectura | Alineado |
| Costos | Admin: `C,R,U,D`; Prod: `L`; Ventas: `L` | Endpoints actuales de costos son `read/export`; Admin lectura/export (y permisos preparados), Prod/Ventas lectura/export | Alineado a capacidades actuales |
| Reportes | Admin: `CT`; Prod/Ventas: `CP` | Admin: `read/export/refresh`; Prod/Ventas: `read` | Alineado |
| Dashboard | Admin: `CT`; Prod/Ventas: `CP` | `dashboard.read` para Admin/Prod/Ventas | Alineado |
| Ecommerce | Admin: `ADM`; Cliente: `UC` | `ecommerce.manage` preparado para Admin; flujo cliente público sin cuenta | Alineado con ajuste de alcance |
| Auditoría | Admin: `L` | `audit.read` preparado para Admin | Alineado |

## Por qué cada rol tiene esos accesos

- `Administrador`: gobierno total del sistema y configuración; se restringe de forma intencional en operaciones de venta transaccional (`sales.create/update`, `customer_orders.create/update`) para preservar segregación operativa.
- `Producción`: foco en operación de fábrica (materia prima, BOM, órdenes de producción, productos), con lectura transversal de módulos necesarios para ejecutar.
- `Ventas`: foco en operación comercial (POS, checkout, órdenes de cliente), con lectura de inventario/producción/costos/reportes para cotizar y cerrar ventas.
- `Cliente`: en esta fase se maneja como rol canónico reservado; el e-commerce opera público (sin cuenta autenticada), por eso no se habilita aún un flujo de autenticación de cliente interno.

## Acciones extra consideradas

Además de la matriz del PDF, se incorporaron explícitamente acciones de negocio extra:

- `*.export` en módulos donde aplica operación real.
- `reports.refresh` solo para administración.
- Acciones dinámicas por request en operaciones bulk (`activate`, `deactivate`, `export`).
- Acciones críticas de venta/orden (`sales.checkout`, `customer_orders.send_to_production`) bajo permisos de Ventas.

## Capa reusable

Definida en `app/rbac.py`:

- `require_permission("modulo.accion")`
- `require_dynamic_permission(resolver_fn)`
- `can("modulo.accion")`
- `can_any("perm.a", "perm.b")`
- Matriz central `ROLE_PERMISSIONS`
- Mapa central de políticas por endpoint `ENDPOINT_PERMISSION_MAP`

## Enforzamiento global

`register_rbac(app)` registra un `before_request` que:

1. Aplica RBAC en rutas internas (`/admin`).
2. Exige autenticación.
3. Evalúa permisos por endpoint.
4. Deniega por defecto endpoints internos sin política explícita.

## Migración y datos base

- Migración idempotente de roles canónicos:
  - `migrations/versions/3f9a8d2c7b11_ensure_canonical_rbac_roles.py`
- Seed de usuarios base por rol:
  - `scripts/seed_users_by_role.py`

## Decisión final de diseño

Con base en el PDF validado y el alcance actual del sistema:

- Se mantienen los 4 roles canónicos existentes.
- No se crean roles nuevos.
- No se requieren cambios adicionales de permisos por ahora.
