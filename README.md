# Sistema de Gestión de Mueblería

Aplicación desarrollado en **Flask** para la gestión del proceso productivo de una mueblería, permitiendo administrar:

* Inventario de materia prima (madera e insumos)
* Inventario de productos terminados (mesas, sillas, closets, etc.)
* Catálogos (tipos de madera, colores, tipos de muebles)
* Procesos de producción
* Control de inventario y trazabilidad

Este sistema forma parte de un proyecto académico orientado a la industria de transformación, donde se controla el flujo
desde la materia prima hasta el producto terminado.

---

## 🛠️ Tecnologías Utilizadas

* Python 3.10.11
* Flask
* Flask-SQLAlchemy
* Flask-WTF (Formularios y CSRF)
* Jinja2 (motor de templates)
* Base de datos relacional (MySQL)
* pip
* Virtual Environment (venv)
* Cloudinary (Gestión de imágenes en la nube)

---

## 🐍 Requisitos

Este proyecto requiere:

* **Python 3.10.11**
* pip

Verificar versión instalada:

```bash
python --version
```

Debe mostrar:

```bash
Python 3.10.11
```

---

## ⚙️ Configuración del Entorno

### 1️⃣ Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd muebles-roble-diseno-app
```

---

### 2️⃣ Crear entorno virtual

```bash
python -m venv venv
```

---

### 3️⃣ Activar entorno virtual

### En Windows:

```bash
venv\Scripts\activate
```

### En Mac/Linux:

```bash
source venv/bin/activate
```

Si se activó correctamente, verás `(venv)` al inicio de la consola.

---

### 4️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ⚙️ Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

- `.env-template` para referencia. Configurar las variables necesarias.
- No eliminar el archivo `.env-template`, solo copiar su estructura para crear `.env`.
- No subir el archivo `.env` al repositorio, ya que contiene información sensible.

Variables clave para 2FA con recuperación por correo (Brevo):

- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`
- `MAIL_USERNAME`, `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`, `SECURITY_EMAIL_SENDER`
- `SECURITY_TWO_FACTOR_RESCUE_MAIL`

Variables para reportes (MongoDB):

- `MONGO_URI`: cadena de conexión de MongoDB para snapshots analíticos.
- `MONGO_DBNAME`: nombre de la base de datos MongoDB donde se almacenan reportes.

Variables para integraciones externas:

- `CLOUDINARY_URL`: URL de configuración para Cloudinary, incluyendo credenciales de API.

### Error común en Reportes: `KeyError: 'mongo_client'`

Si al entrar a `/admin/reports` aparece este error, normalmente el entorno local no tiene
configuradas las variables de MongoDB (`MONGO_URI` y `MONGO_DBNAME`) o MongoDB no está disponible.

El módulo de reportes inicializa el cliente de MongoDB de forma automática en
`app/reports/mongo_service.py`, pero requiere esas variables para conectar y persistir snapshots.

---

## 🔌 Integraciones y APIs Externas

El proyecto hace uso de servicios externos para enriquecer sus funcionalidades:

* **Brevo (SMTP / Envío de Correos):** Se utiliza la plataforma de Brevo como puente SMTP seguro para el envío de correos electrónicos transaccionales institucionales (ej. códigos de autenticación 2FA, recuperación de contraseñas y correos de confirmación / tickets de compra).
* **COPOMEX API:** Se integra esta API de códigos postales mexicanos dentro del módulo de ventas (POS y E-Commerce). Permite buscar códigos postales para autocompletar asentamientos y, principalmente, automatizar el cálculo logístico del costo de flete (envío) según la zona o colonia de destino del cliente.
* **Cloudinary:** Servicio de gestión de imágenes en la nube utilizado para almacenar y gestionar las imágenes de productos. Permite subir imágenes de productos al crear o editar productos, y eliminarlas cuando se remueven. Las imágenes se almacenan de forma segura en la nube y se accede a ellas mediante URLs generadas por Cloudinary.

---

## ▶️ Ejecutar el Proyecto

Si usas Flask CLI:

```bash
flask run
```

O directamente:

```bash
python run.py
```

El servidor iniciará en:

```
http://127.0.0.1:5000
```

---

## 🌱 Datos Iniciales (Seeds)

El dataset inicial oficial de categorias, productos, colores, tipos de madera, BOM y costos se define en:

- `docs/INITIAL_SEED_BLUEPRINT.md`

Orden recomendado de siembra:

```bash
venv/bin/python scripts/seed_units.py
venv/bin/python scripts/seed_raw_materials.py
venv/bin/python scripts/seed_wood_types.py
venv/bin/python scripts/seed_products.py
venv/bin/python scripts/seed_product_colors.py
venv/bin/python scripts/seed_payment_methods.py
venv/bin/python scripts/seed_purchase.py
venv/bin/python scripts/seed_bom.py
venv/bin/python scripts/seed_inventory.py
venv/bin/python scripts/seed_users_by_role.py
```

Opción rápida (una sola corrida):

```bash
venv/bin/python scripts/seed_all.py
```

Opcional (si no quieres crear usuarios RBAC en esa corrida):

```bash
venv/bin/python scripts/seed_all.py --without-users
```

Notas:

- Los scripts estan disenados para ser idempotentes en entorno de desarrollo.
- `Muebles personalizados` permanece como categoria activa sin productos iniciales (intencional).
- El costo de fabricacion depende de la cadena `BOM + purchase_order_items`.

---

## 🧪 Pruebas y Cobertura

El proyecto incluye una suite completa de pruebas automatizadas con **138 tests** organizados en tres niveles:

| Tipo | Directorio | Propósito |
|------|-----------|-----------|
| **Unitarias** | `tests/unit/` | Lógica de negocio de services y modelos |
| **Integración** | `tests/integration/` | Rutas HTTP, protección de autenticación |
| **E2E** | `tests/e2e/` | Flujos completos multi-paso (checkout) |

### ▶️ Cómo Ejecutar las Pruebas

> **Importante:** Siempre activar el entorno virtual antes de ejecutar pruebas.

```bash
# Activar entorno virtual
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Ejecutar todas las pruebas
python -m pytest tests/ -v

# Ejecutar solo un tipo de prueba
python -m pytest tests/unit/ -v           # Solo unitarias
python -m pytest tests/integration/ -v    # Solo integración
python -m pytest tests/e2e/ -v            # Solo E2E

# Ejecutar un archivo específico
python -m pytest tests/unit/test_inventory_service.py -v
```

### 📊 Cobertura de Código (Coverage)

```bash
# Ejecutar con reporte de cobertura en terminal
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Generar reporte HTML interactivo
python -m pytest tests/ --cov=app --cov-report=html
```

Después del último comando, abrir `htmlcov/index.html` en el navegador para ver el reporte visual de cobertura línea por línea.

### 📁 Estructura de Tests

```
tests/
├── conftest.py                             # Fixtures compartidas (app, DB, seed data)
├── unit/
│   ├── test_inventory_service.py           # InventoryService (descuento de stock)
│   ├── test_ecommerce_service.py           # EcommerceService (carrito, IVA, checkout)
│   ├── test_sale_service.py                # SaleService POS (ventas, items, clientes)
│   ├── test_customer_order_service.py      # CustomerOrderService (órdenes, estados)
│   └── test_models.py                      # Modelos (serialización, propiedades)
├── integration/
│   ├── test_ecommerce_routes.py            # Rutas ecommerce (páginas, carrito, API)
│   └── test_admin_routes.py                # Panel admin (auth, POS API, órdenes)
└── e2e/
    └── test_ecommerce_checkout_flow.py     # Flujo completo de compra
```

### ⚙️ Configuración de Tests

Los tests usan **SQLite in-memory** (no requieren MySQL). La configuración está en:

- `config.py` → clase `TestingConfig`
- `pyproject.toml` → secciones `[tool.pytest]` y `[tool.coverage]`
- `tests/conftest.py` → fixtures de app, base de datos y datos semilla

---

## 🔍 Control de Calidad de Código

Este proyecto incluye herramientas automáticas para mantener la calidad del código:

### 📋 Herramientas Configuradas

| Herramienta | Descripción                                  | Comando                    |
|-------------|----------------------------------------------|----------------------------|
| **Black**   | Formateador de código Python                 | `black .`                  |
| **Ruff**    | Linter rápido para Python                    | `ruff check .`             |
| **Mypy**    | Verificador de tipos estático                | `mypy app/`                |
| **djLint**  | Formateador de templates HTML                | `djlint app/templates/`    |

### 🚀 Ejecución Local de Checks

Antes de hacer commit, ejecuta los siguientes comandos para asegurar la calidad:

```bash
# Formatear código con Black
black .

# Verificar linting con Ruff
ruff check .

# Verificar tipos con Mypy
mypy app/ --config-file=mypy.ini

# Lint y formatear templates HTML
djlint app/templates/ --lint
djlint app/templates/ --reformat
```

### 🤖 CI/CD Automático

El proyecto utiliza **GitHub Actions** para ejecutar estos checks automáticamente en:

- ✅ Push a `main` o `dev`
- ✅ Pull Requests a `main` o `dev`
- ✅ Push de tags semánticos `vX.Y.Z` (ejemplo: `v1.2.0`)

El workflow (`.github/workflows/ci.yml`) ejecuta **3 jobs en paralelo**:

| Job | Qué hace |
|-----|----------|
| **Code Quality** | Black, Ruff, Mypy, djLint |
| **Security** | Bandit (análisis de seguridad) |
| **Tests & Coverage** | `pytest` con cobertura mínima del 40% |

Los reportes de cobertura HTML y resultados JUnit XML se suben como **artifacts** descargables desde la pestaña Actions de GitHub.

Adicionalmente, al hacer push de un tag `vX.Y.Z`, se crea un **GitHub Release** automáticamente mediante `.github/workflows/release.yml`.

### 🏷️ Versionado con Tags en CI

Para versionar cambios del proyecto en CI, usa tags semánticos con prefijo `v`:

```bash
# Crear tag anotado
git tag -a v1.0.0 -m "Release v1.0.0"

# Publicar un tag específico
git push origin v1.0.0

# (Opcional) Publicar todos los tags locales
git push origin --tags
```

Cuando el workflow corre por tag, los artefactos se publican con ese identificador de versión (por ejemplo `quality-reports-v1.0.0`).

### 🔐 Pre-commit Hooks

Opcionalmente, puedes instalar pre-commit hooks para ejecutar estos checks antes de hacer commit:

```bash
# Instalar pre-commit hooks
pre-commit install

# (Los hooks se ejecutarán automáticamente al hacer git commit)
```

---

## 📂 Estructura del Proyecto

```
muebles-roble-diseno-app/
│
├── app/                          # Paquete principal de la aplicación
│   ├── __init__.py               # Factory de la aplicación Flask (create_app)
│   ├── extensions.py             # Extensiones de Flask (SQLAlchemy, Migrate, CSRF)
│   ├── exceptions.py             # Excepciones personalizadas y manejo de errores
│   │
│   ├── catalogs/                 # Módulo de catálogos
│   │   └── colors/               # Submódulo de colores
│   │       ├── __init__.py
│   │       ├── routes.py         # Rutas y controladores
│   │       ├── services.py       # Lógica de negocio
│   │       └── forms.py          # Formularios con WTForms
│   │
│   ├── models/                   # Capa de modelos (entidades de BD)
│   │   └── color.py              # Modelo de Color
│   │
│   └── templates/                # Templates Jinja2
│       ├── layouts/
│       │   ├── store.html
│       │   └── admin.html
│       │
│       ├── store/
│       │   ├── home.html
│       │   ├── product_detail.html
│       │   └── cart.html
│       │
│       ├── admin/
│       │   ├── dashboard.html
│       │   └── catalogs/
│       │       └── colors/
│       │           ├── list.html
│       │           ├── create.html
│       │           └── edit.html
│       │
│       └── components/
│           ├── forms/
│           │   ├── input.html
│           │   ├── select.html
│           │   └── textarea.html
│           │
│           ├── tables/
│           │   └── table.html
│           │
│           ├── ui/
│           │   ├── button.html
│           │   ├── badge.html
│           │   ├── alert.html
│           │   ├── modal.html
│           │   └── card.html
│           │
│           ├── ecommerce/
│           │   ├── product_card.html
│           │   ├── price_tag.html
│           │   ├── rating_stars.html
│           │   └── add_to_cart_button.html
│           │
│           └── admin/
│               ├── sidebar.html
│               ├── navbar.html
│               └── stats_card.html
│
├── docs/                         # Documentación del proyecto
│   ├── ARCHITECTURE.md           # Documentación de arquitectura
│   └── CODING_CONVENTIONS.md     # Convenciones de código
│
├── config.py                     # Configuración del proyecto (Config, TestingConfig)
├── run.py                        # Punto de entrada de la aplicación
├── requirements.txt              # Dependencias del proyecto
├── .env                          # Variables de entorno (no versionar)
├── .env-template                 # Plantilla de variables de entorno
├── tests/                        # Suite de pruebas automatizadas
│   ├── conftest.py               # Fixtures compartidas
│   ├── unit/                     # Pruebas unitarias (services, models)
│   ├── integration/              # Pruebas de integración (rutas HTTP)
│   └── e2e/                      # Pruebas end-to-end (flujos completos)
├── htmlcov/                      # Reportes de cobertura HTML (no versionar)
└── README.md
```

---

## 🏗️ Arquitectura MVC en Capas

El proyecto está diseñado siguiendo una **arquitectura MVC en capas** con Jinja2 como motor de templates para separar
responsabilidades y facilitar el mantenimiento:

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                     │
│               (routes.py + templates Jinja2)                │
│          Rutas / Controladores / Vistas HTML                │
├─────────────────────────────────────────────────────────────┤
│                  CAPA DE LÓGICA DE NEGOCIO                  │
│                      (services.py)                          │
│     Reglas de negocio / Validaciones / Procesamiento        │
├─────────────────────────────────────────────────────────────┤
│                    CAPA DE DATOS/MODELOS                    │
│                       (models/)                             │
│          Entidades / ORM SQLAlchemy / Base de Datos         │
└─────────────────────────────────────────────────────────────┘
```

### 📁 Descripción de Capas

| Capa              | Archivos                        | Responsabilidad                                                                             |
|-------------------|-------------------------------- |---------------------------------------------------------------------------------------------|
| **Presentación**  | `routes.py` + `templates/`      | Define las rutas, recibe peticiones HTTP y renderiza vistas HTML con Jinja2                 |
| **Servicios**     | `services.py`                   | Contiene la lógica de negocio, validaciones y orquestación de operaciones                   |
| **Modelos**       | `models/*.py`                   | Define las entidades y su mapeo a tablas de base de datos usando SQLAlchemy ORM             |
| **Configuración** | `config.py`, `extensions.py`    | Configuración del entorno, conexión a BD y extensiones de Flask                             |

### 📦 Organización por Módulos

El proyecto organiza las funcionalidades en **módulos de dominio** dentro de `app/`:

```
app/
├── catalogs/           # Catálogos del sistema
│   ├── colors/         # Gestión de colores
│   ├── wood_types/     # Tipos de madera (futuro)
│   └── furniture_types/# Tipos de muebles (futuro)
│
├── inventory/          # Control de inventario (futuro)
├── production/         # Procesos de producción (futuro)
└── models/             # Todos los modelos de la aplicación
```

### 🔄 Flujo de una Petición

```
Navegador Web
     │
     ▼
┌─────────────┐
│  routes.py  │  ← Recibe la petición, procesa formularios
└─────────────┘
     │
     ▼
┌─────────────┐
│ services.py │  ← Ejecuta lógica de negocio
└─────────────┘
     │
     ▼
┌─────────────┐
│  models/    │  ← Interactúa con la base de datos
└─────────────┘
     │
     ▼
  Base de Datos (MySQL)
     │
     ▼
┌─────────────┐
│ template.html│ ← Renderiza vista HTML con Jinja2
└─────────────┘
     │
     ▼
  Navegador Web
```

---

## 📚 Documentación Adicional

| Documento                                               | Descripción                                         |
|---------------------------------------------------------|-----------------------------------------------------|
| [🛠️ Herramientas de Desarrollo](docs/DEVELOPMENT_TOOLS.md) | Herramientas de calidad, CI/CD y pre-commit        |
| [📐 Arquitectura](docs/ARCHITECTURE.md)                 | Documentación detallada de la arquitectura en capas |
| [📋 Convenciones de Código](docs/CODING_CONVENTIONS.md) | Estándares y convenciones de desarrollo             |
| [🔐 RBAC](docs/RBAC.md)                                 | Matriz de permisos, utilidades y enforcement global |

---

## 📊 Funcionalidades Principales

* Gestión de tipos de madera (Pino, Cedro, Encino)
* Gestión de colores (Natural, Blanco, Negro, etc.)
* Registro de muebles (Mesas, Sillas, Closets, etc.)
* Control de inventario de materia prima
* Registro de producción
* Control de productos terminados
* Auditoría de operaciones

---

## 🚫 Importante

- El archivo `.gitignore` se debe de editar con precaución.
- Actualizar el README para documentar el proyecto.

---

## 👤 Autor

Lattice Systems

Ingeniería en Desarrollo y Gestión de Software
Sistema de Gestión de Mueblería
