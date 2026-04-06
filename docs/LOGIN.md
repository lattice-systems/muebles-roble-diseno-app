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
5. Si se alcanzan 3 intentos fallidos:
- Se bloquea el `POST /login` con respuesta `429`.
- Se registra evento `auth.account.locked`.
- No se incrementa mas el contador mientras la solicitud este bloqueada.
 - El desbloqueo es automatico al expirar la ventana de bloqueo (default 15 minutos).
 - Al expirar, se registra `auth.account.unlocked.auto`.
6. En logout (`POST /login/logout`):
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
- `auth.account.locked`
 - `auth.account.unlocked.auto`

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
- Límite actual: `3` intentos (`SECURITY_MAX_LOGIN_ATTEMPTS`, default 3).
 - Ventana de bloqueo: `15` minutos (`SECURITY_LOGIN_LOCK_MINUTES`, default 15).
- Se reinicia en login exitoso.

## Seguridad de visualizacion

- Los logs tecnicos no se exponen al cliente final.
- Los eventos de seguridad son para admins/soporte autorizado.
- Auditoria de negocio y auditoria de seguridad deben mantenerse separadas.

## Validacion recomendada

1. Intentar login invalido tres veces.
2. Verificar en `security_event_log` filas `auth.login.failed` con intentos 1, 2 y 3 en `context_data.attempt`.
3. Intentar login nuevamente y validar respuesta `429`.
4. Verificar fila `auth.account.locked`.
5. Esperar expiracion de ventana y reintentar login.
6. Verificar fila `auth.account.unlocked.auto`.
7. Hacer login valido y verificar `auth.login.success`.
8. Ejecutar logout y verificar `auth.logout`.
