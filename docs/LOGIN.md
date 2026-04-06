# Modulo de Login y Seguridad

## Objetivo

Definir el flujo de autenticacion, cierre de sesion y registro de eventos de seguridad para el sistema administrativo.

## Flujo funcional actual

1. Usuario solicita `/login`.
2. Flask-Security renderiza y procesa el formulario de autenticacion.
3. Si las credenciales son validas:
- Se autentica la sesion.
- Se registra evento `auth.login.success`.
- Se reinicia el contador de intentos fallidos en sesion.
4. Si las credenciales son invalidas:
- Se mantiene el usuario anonimo.
- Se incrementa el contador de intentos en sesion (`security_login_attempts`).
- Se registra evento `auth.login.failed` con numero de intento.
5. En logout (`POST /login/logout`):
- Se cierra sesion, se limpian cookies/sesion y cache headers.
- Se registra evento `auth.logout`.

## Rutas relevantes

- `GET /login/`: redirige al endpoint de Flask-Security (`security.login`).
- `POST /login`: autenticacion (gestionada por Flask-Security).
- `POST /login/logout`: cierre de sesion seguro.

## Eventos de seguridad implementados

- `auth.login.success`
- `auth.login.failed`
- `auth.logout`
- `auth.password.changed`
- `auth.password.reset.completed`
- `auth.unauthenticated.access`

## Persistencia

Todos los eventos anteriores se almacenan en `security_event_log` con:

- `event_type`
- `result`
- `user_id` (cuando aplica)
- `email_or_identifier`
- `ip_address`
- `user_agent`
- `reason`
- `context_data`
- `source`
- `timestamp`

## Contador de intentos de sesion

Se guarda por sesion en la clave:

- `security_login_attempts`

Comportamiento:

- Incrementa en cada `POST /login` fallido.
- Se reinicia en login exitoso.

## Seguridad de visualizacion

- Los logs tecnicos no se exponen al cliente final.
- Los eventos de seguridad son para admins/soporte autorizado.
- Auditoria de negocio y auditoria de seguridad deben mantenerse separadas.

## Validacion recomendada

1. Intentar login invalido dos veces.
2. Verificar en `security_event_log` dos filas `auth.login.failed` con intentos 1 y 2 en `context_data.attempt`.
3. Hacer login valido.
4. Verificar fila `auth.login.success` y reinicio del contador de intentos.
5. Ejecutar logout y verificar `auth.logout`.
