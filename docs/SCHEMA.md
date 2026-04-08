# Sistema de Gestión de Producción y Ventas – Manufactura de Muebles

## 1. Descripción general

Este documento describe la estructura de la base de datos transaccional (MySQL) del sistema de gestión para una empresa
manufacturera de muebles.

La base de datos soporta los procesos de:

* Gestión de usuarios
* Inventario de materia prima
* Compras y proveedores
* Producción
* Explosión de materiales (BOM)
* Inventario de productos terminados
* Ventas POS
* Ecommerce
* Costos
* Reportes
* Auditoría

La base de datos sigue un modelo OLTP relacional, garantizando integridad referencial, consistencia y transacciones
ACID. Las consultas analíticas y reportes se almacenan posteriormente en una base de datos NoSQL para OLAP.

---

## 2. Convenciones de nomenclatura

| Elemento             | Convención                  |
|:---------------------|:----------------------------|
| **Tablas**           | `snake_case`                |
| **Columnas**         | `snake_case`                |
| **Claves primarias** | `id`                        |
| **Claves foráneas**  | `nombre_tabla_id`           |
| **Fechas**           | `created_at` / `updated_at` |
| **Estados**          | `status`                    |

---

## 3. Módulo de Usuarios y Seguridad

Este módulo implementa RBAC (Role Based Access Control) para restringir acceso según el rol del usuario.

### Tabla: `roles`

Define los roles del sistema (Ejemplos: administrador, produccion, ventas, cliente).

| Campo         | Tipo     | Descripción           |
|:--------------|:---------|:----------------------|
| `id`          | INT PK   | Identificador del rol |
| `name`        | VARCHAR  | Nombre del rol        |
| `description` | TEXT     | Descripción del rol   |
| `created_at`  | DATETIME | Fecha de creación     |

### Tabla: `users`

Usuarios del sistema (administradores, empleados o clientes).

| Campo           | Tipo     | Descripción               |
|:----------------|:---------|:--------------------------|
| `id`            | INT PK   | Identificador del usuario |
| `full_name`     | VARCHAR  | Nombre completo           |
| `email`         | VARCHAR  | Correo electrónico        |
| `password_hash` | VARCHAR  | Contraseña cifrada        |
| `role_id`       | FK       | Rol asignado (`roles.id`) |
| `status`        | BOOLEAN  | Estado activo/inactivo    |
| `created_at`    | DATETIME | Fecha de creación         |

---

## 4. Módulo de Catálogos

Los catálogos son tablas de referencia utilizadas en inventario, productos y ventas.

### Tabla: `wood_types`

Tipos de madera utilizados en los muebles.

| Campo         | Tipo    | Descripción               |
|:--------------|:--------|:--------------------------|
| `id`          | PK      | Identificador             |
| `name`        | VARCHAR | Nombre del tipo de madera |
| `description` | TEXT    | Características           |
| `status`      | BOOLEAN | Estado activo             |

### Tabla: `colors`

Colores disponibles para los productos.

| Campo      | Tipo    | Descripción      |
|:-----------|:--------|:-----------------|
| `id`       | PK      | Identificador    |
| `name`     | VARCHAR | Nombre del color |
| `hex_code` | VARCHAR | Código visual    |
| `status`   | BOOLEAN | Estado           |

### Tabla: `furniture_types`

Clasificación de muebles.

| Campo         | Tipo    | Descripción    |
|:--------------|:--------|:---------------|
| `id`          | PK      | Identificador  |
| `name`        | VARCHAR | Tipo de mueble |
| `description` | TEXT    | Descripción    |

### Tabla: `units`

Unidades de medida utilizadas en inventario.

| Campo          | Tipo    | Descripción                   |
|:---------------|:--------|:------------------------------|
| `id`           | PK      | Identificador                 |
| `name`         | VARCHAR | Nombre                        |
| `abbreviation` | VARCHAR | Abreviatura                   |
| `type`         | VARCHAR | Tipo (peso, longitud, unidad) |

### Tabla: `payment_methods`

Métodos de pago aceptados.

| Campo  | Tipo    | Descripción                             |
|:-------|:--------|:----------------------------------------|
| `id`   | PK      | Identificador                           |
| `name` | VARCHAR | Método de pago                          |
| `type` | VARCHAR | Tipo (efectivo, tarjeta, transferencia) |

---

## 5. Módulo de Proveedores y Compras

Gestiona el abastecimiento de materias primas.

### Tabla: `suppliers`

Información de proveedores.

| Campo     | Tipo    | Descripción      |
|:----------|:--------|:-----------------|
| `id`      | PK      | Identificador    |
| `name`    | VARCHAR | Nombre proveedor |
| `phone`   | VARCHAR | Teléfono         |
| `email`   | VARCHAR | Correo           |
| `address` | TEXT    | Dirección        |
| `status`  | BOOLEAN | Estado           |

### Tabla: `purchase_orders`

Órdenes de compra.

| Campo         | Tipo    | Descripción                |
|:--------------|:--------|:---------------------------|
| `id`          | PK      | Identificador              |
| `supplier_id` | FK      | Proveedor (`suppliers.id`) |
| `order_date`  | DATE    | Fecha de orden             |
| `status`      | VARCHAR | Estado                     |
| `total`       | DECIMAL | Total                      |

### Tabla: `purchase_order_items`

Detalle de compra.

| Campo               | Tipo    | Descripción                            |
|:--------------------|:--------|:---------------------------------------|
| `id`                | PK      | Identificador                          |
| `purchase_order_id` | FK      | Orden de compra (`purchase_orders.id`) |
| `raw_material_id`   | FK      | Materia prima (`raw_materials.id`)     |
| `quantity`          | DECIMAL | Cantidad                               |
| `unit_price`        | DECIMAL | Precio unitario                        |

---

## 6. Inventario de Materia Prima

Controla insumos utilizados en producción.

### Tabla: `raw_materials`

Registro de materias primas.

| Campo              | Tipo    | Descripción                   |
|:-------------------|:--------|:------------------------------|
| `id`               | PK      | Identificador                 |
| `name`             | VARCHAR | Nombre                        |
| `unit_id`          | FK      | Unidad de medida (`units.id`) |
| `waste_percentage` | DECIMAL | Merma                         |
| `stock`            | DECIMAL | Existencia actual             |

### Tabla: `raw_material_movements`

Movimientos de inventario.

| Campo             | Tipo     | Descripción                        |
|:------------------|:---------|:-----------------------------------|
| `id`              | PK       | Identificador                      |
| `raw_material_id` | FK       | Materia prima (`raw_materials.id`) |
| `movement_type`   | VARCHAR  | Tipo (entrada / salida)            |
| `quantity`        | DECIMAL  | Cantidad                           |
| `reference`       | VARCHAR  | Referencia (compra, producción)    |
| `created_at`      | DATETIME | Fecha                              |

---

## 7. Productos Terminados

Productos listos para venta.

### Tabla: `products`

| Campo               | Tipo    | Descripción                           |
|:--------------------|:--------|:--------------------------------------|
| `id`                | PK      | Identificador                         |
| `sku`               | VARCHAR | Código único                          |
| `name`              | VARCHAR | Nombre del producto                   |
| `furniture_type_id` | FK      | Tipo de mueble (`furniture_types.id`) |
| `description`       | TEXT    | Descripción                           |
| `price`             | DECIMAL | Precio de venta                       |
| `status`            | BOOLEAN | Activo/inactivo                       |

### Tabla: `product_colors`

Variantes de color del producto.

| Campo        | Tipo | Descripción              |
|:-------------|:-----|:-------------------------|
| `id`         | PK   | Identificador            |
| `product_id` | FK   | Producto (`products.id`) |
| `color_id`   | FK   | Color (`colors.id`)      |

### Tabla: `product_inventory`

Inventario de productos terminados.

| Campo        | Tipo | Descripción              |
|:-------------|:-----|:-------------------------|
| `id`         | PK   | Identificador            |
| `product_id` | FK   | Producto (`products.id`) |
| `stock`      | INT  | Existencias              |

---

## 8. BOM (Bill of Materials)

Define la receta de fabricación.

### Tabla: `bom`

Receta de producción.

| Campo         | Tipo    | Descripción              |
|:--------------|:--------|:-------------------------|
| `id`          | PK      | Identificador            |
| `product_id`  | FK      | Producto (`products.id`) |
| `version`     | VARCHAR | Versión                  |
| `description` | TEXT    | Descripción              |

### Tabla: `bom_items`

Insumos requeridos.

| Campo               | Tipo    | Descripción                        |
|:--------------------|:--------|:-----------------------------------|
| `id`                | PK      | Identificador                      |
| `bom_id`            | FK      | Receta (`bom.id`)                  |
| `raw_material_id`   | FK      | Materia prima (`raw_materials.id`) |
| `quantity_required` | DECIMAL | Cantidad necesaria                 |

---

## 9. Producción

Gestiona la fabricación.

### Tabla: `production_orders`

| Campo            | Tipo    | Descripción                               |
|:-----------------|:--------|:------------------------------------------|
| `id`             | PK      | Identificador                             |
| `product_id`     | FK      | Producto (`products.id`)                  |
| `quantity`       | INT     | Cantidad a producir                       |
| `status`         | VARCHAR | Estado (pendiente / proceso / finalizado) |
| `scheduled_date` | DATE    | Fecha programada                          |

---

## 10. Ventas

Ventas físicas POS.

### Tabla: `sales`

| Campo               | Tipo     | Descripción                           |
|:--------------------|:---------|:--------------------------------------|
| `id`                | PK       | Identificador                         |
| `sale_date`         | DATETIME | Fecha                                 |
| `total`             | DECIMAL  | Total                                 |
| `payment_method_id` | FK       | Método de pago (`payment_methods.id`) |

### Tabla: `sale_items`

| Campo        | Tipo    | Descripción              |
|:-------------|:--------|:-------------------------|
| `id`         | PK      | Identificador            |
| `sale_id`    | FK      | Venta (`sales.id`)       |
| `product_id` | FK      | Producto (`products.id`) |
| `quantity`   | INT     | Cantidad                 |
| `price`      | DECIMAL | Precio                   |

---

## 11. Ecommerce

Ventas en línea.

* **Tabla: `customers`** - Clientes del ecommerce.
* **Tabla: `orders`** - Pedidos online.
* **Tabla: `order_items`** - Detalle del pedido.

---

## 12. Auditoría

Registra operaciones críticas del sistema para trazabilidad.

### Tabla: `audit_log`

| Campo           | Tipo     | Descripción                                |
|:----------------|:---------|:-------------------------------------------|
| `id`            | PK       | Identificador                              |
| `table_name`    | VARCHAR  | Tabla afectada                             |
| `action`        | VARCHAR  | INSERT / UPDATE / DELETE                   |
| `user_id`       | FK       | Usuario que realizó la acción (`users.id`) |
| `record_id`     | VARCHAR  | ID del registro afectado (PK lógica)       |
| `source`        | VARCHAR  | Origen del evento (`application`/`db_trigger`) |
| `timestamp`     | DATETIME | Fecha                                      |
| `previous_data` | JSON     | Datos anteriores                           |
| `new_data`      | JSON     | Datos nuevos                               |

**Índices recomendados para consulta operativa:**

* `ix_audit_log_timestamp`
* `ix_audit_log_table_timestamp`
* `ix_audit_log_user_timestamp`

---

## 13. Consideraciones de diseño

**Buenas prácticas aplicadas:**

* Integridad referencial mediante foreign keys (`FK`).
* Uso de tablas de catálogo.
* Separación entre inventario, producción y ventas.
* Auditoría para trazabilidad.
* Preparación para analítica en NoSQL.

**Esto permite soportar:**

* Control completo de inventario.
* Producción basada en BOM (Bill of Materials).
* Omnicanalidad POS + ecommerce.
* Reportes financieros y operativos.