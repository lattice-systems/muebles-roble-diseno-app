# Modulo de Auditoria

## Objetivo

Centralizar la trazabilidad de operaciones criticas con evidencia util para:

- Control interno y cumplimiento academico (uso de triggers MySQL).
- Analisis forense de incidentes.
- Soporte a operaciones (quien, que, cuando y sobre que registro).

## Tabla audit_log (campos utiles)

- `id`: identificador del evento.
- `table_name`: tabla afectada.
- `action`: `INSERT`, `UPDATE`, `DELETE`.
- `user_id`: usuario asociado al cambio.
- `record_id`: id del registro afectado.
- `source`: origen (`application` o `db_trigger`).
- `timestamp`: marca temporal del evento.
- `previous_data`: snapshot previo (JSON).
- `new_data`: snapshot nuevo (JSON).

Indices operativos:

- `ix_audit_log_timestamp`
- `ix_audit_log_table_timestamp`
- `ix_audit_log_user_timestamp`

## Triggers MySQL

La estrategia principal es por trigger `AFTER INSERT/UPDATE/DELETE` para cada tabla de negocio (excepto `audit_log` y `alembic_version`).

El trigger inserta en `audit_log`:

- Tabla y accion.
- Usuario inferido por columnas de auditoria (`created_by`, `updated_by`, etc.) y por variable de sesion `@audit_user_id` si existe.
- Snapshot JSON del registro completo antes/despues.

## Politica anti-duplicados

Para evitar eventos duplicados en MySQL:

- En MySQL, la fuente primaria es `db_trigger`.
- La auditoria desde servicios Python se registra solo como fallback cuando el dialecto NO es MySQL (por ejemplo SQLite en tests).

Implementacion central:

- Helper: `app/shared/audit_logging.py`
- Funcion: `log_application_audit(...)`

Overrides opcionales por configuracion:

- `AUDIT_FORCE_APPLICATION_LOGS`
- `AUDIT_ENABLE_APPLICATION_FALLBACK`

## Alcance minimo recomendado de auditoria

- Usuarios y roles.
- Catalogos.
- Proveedores, compras y materia prima.
- Productos, inventario y produccion.
- Ventas y ordenes de cliente.
- Cualquier tabla que impacte stock, costos o estado de orden.

## Modulo de control

Ruta admin:

- `GET /admin/audit`: listado con filtros (tabla, accion, fuente, usuario y rango de fechas).
- `GET /admin/audit/<id>/details`: detalle amigable por campo y JSON tecnico opcional.

Seguridad de datos sensibles en detalle:

- Nunca se exponen credenciales o secretos en texto claro ni en hash visible.
- Campos sensibles (ejemplo: `password_hash`, `password`, `fs_uniquifier`, `tf_totp_secret`) se muestran como `Oculto (dato sensible)`.
- El bloque JSON tecnico del detalle tambien aplica redaccion (`[REDACTED]`) para esos campos.

Permiso RBAC:

- `audit.read`.

## Testing minimo recomendado

- RBAC: solo `admin` con `audit.read`.
- Integracion: ruta `/admin/audit` requiere autenticacion.
- Unitario: filtros de `AuditService` y consulta de detalle.

## Estructura recomendada (separacion por tipo de registro)

### 1) Auditoria de negocio (para backoffice)

Objetivo:

- Trazar cambios funcionales del sistema (ventas, compras, inventario, catalogos, usuarios, estados).

Fuente:

- Principalmente triggers MySQL sobre tablas de negocio.

Visualizacion:

- Visible solo para personal autorizado (permiso `audit.read`).
- Mostrar resumen amigable: tabla, accion, actor, fecha, cambios por campo.
- Nunca exponer campos sensibles.

Tabla sugerida:

- `audit_log` (actual): `table_name`, `action`, `user_id`, `record_id`, `source`, `timestamp`, `previous_data`, `new_data`.

### 2) Auditoria de seguridad (autenticacion/autorizacion)

Objetivo:

- Registrar eventos de seguridad y acceso.

Eventos recomendados:

- `auth.login.success`
- `auth.login.failed`
- `auth.logout`
- `auth.password.changed`
- `auth.password.reset.requested`
- `auth.password.reset.completed`
- `auth.rbac.denied`
- `auth.account.locked`

Eventos implementados actualmente:

- `auth.login.success` (senal `user_authenticated` de Flask-Security)
- `auth.logout` (senal `user_logged_out` de Flask-Login)
- `auth.password.changed` (senal `password_changed`)
- `auth.password.reset.completed` (senal `password_reset`)
- `auth.unauthenticated.access` (senal `user_unauthenticated`)

Campos sugeridos:

- `event_type`, `user_id` (nullable), `email_or_identifier`, `ip_address`, `user_agent`, `result`, `reason`, `timestamp`, `metadata`.

Campos implementados actualmente en `security_event_log`:

- `event_type`, `result`, `user_id`, `email_or_identifier`, `ip_address`, `user_agent`, `reason`, `context_data`, `source`, `timestamp`.

Tabla sugerida:

- `security_event_log` (separada de `audit_log`).

Visualizacion:

- Solo para administradores de seguridad o soporte avanzado.
- No mostrar al cliente final.

### 3) Logging tecnico (observabilidad)

Objetivo:

- Diagnosticar errores, performance y fallos de infraestructura.

Contenido:

- Errores de aplicacion, excepciones, stack trace, tiempos de respuesta, eventos de integraciones externas.

Destino recomendado:

- Consola/archivo en desarrollo.
- Plataforma de logs en produccion (por ejemplo ELK, Loki, Cloud Logging, Datadog).

Visualizacion:

- Exclusivo para equipo tecnico.
- No mostrar al cliente final ni en pantallas funcionales del negocio.

## Regla de visibilidad por audiencia

- Cliente final: no ve logs internos.
- Usuario administrativo: solo auditoria de negocio relevante al proceso.
- Soporte/seguridad: auditoria de seguridad.
- Equipo tecnico: logs tecnicos completos.

## Scripts operativos

- `scripts/install_audit_triggers.py`: reinstala triggers de auditoria en MySQL.
- Migracion Alembic: `6d0f4b7e2a91_add_audit_trigger_module_and_log_fields.py`.
- Migracion Alembic: `7e11c2a8f4d2_add_security_event_log_table.py`.

## Checklist de despliegue (MySQL)

### 1) Prechecks

- Verificar branch limpio y respaldo de base de datos.
- Confirmar credenciales en `.env` (`DB_*`, `SECRET_KEY`, `SECURITY_PASSWORD_SALT`).
- Asegurar Flask app para comandos de migracion:

```bash
export FLASK_APP=run.py
export FLASK_ENV=production
```

### 2) Migrar esquema

```bash
source venv/bin/activate
flask db upgrade
```

Resultado esperado:

- Tabla `audit_log` con columnas `record_id` y `source`.
- Indices `ix_audit_log_timestamp`, `ix_audit_log_table_timestamp`, `ix_audit_log_user_timestamp`.
- Tabla `security_event_log` con indices por timestamp, tipo de evento y usuario.

### 3) Reinstalar triggers de auditoria

```bash
venv/bin/python scripts/install_audit_triggers.py
```

Resultado esperado:

- Mensaje: `Triggers de auditoria instalados correctamente ...`.

### 4) Verificar triggers instalados

En MySQL:

```sql
SHOW TRIGGERS LIKE '%trg_audit_%';
```

Debe existir trio por tabla auditada:

- `..._ai` (AFTER INSERT)
- `..._au` (AFTER UPDATE)
- `..._ad` (AFTER DELETE)

### 5) Smoke test funcional

1. Crear o editar un registro de un modulo (por ejemplo colores o proveedores).
2. Consultar eventos recientes:

```sql
SELECT id, table_name, action, user_id, record_id, source, timestamp
FROM audit_log
ORDER BY id DESC
LIMIT 20;
```

Resultado esperado:

- Nuevos eventos con `source = 'db_trigger'` en MySQL.
- Sin duplicados `application` + `db_trigger` para la misma operacion.

### 6) Verificar modulo web y RBAC

- Entrar a `/admin/audit` con usuario admin.
- Confirmar acceso denegado para roles sin `audit.read`.
- Validar filtros por tabla, accion, usuario y fechas.

### 7) Rollback (si se requiere)

- Revertir migracion:

```bash
flask db downgrade 6d0f4b7e2a91
```

- Opcion quirurgica: eliminar triggers con `DROP TRIGGER` por nombre afectado.

### 8) Monitoreo posterior

- Revisar crecimiento de `audit_log` y plan de retencion/particionado.
- Monitorear tiempos de escritura en tablas de alto trafico.
