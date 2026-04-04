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

Variables para integraciones externas:

- `CLOUDINARY_URL`: URL de configuración para Cloudinary, incluyendo credenciales de API.

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

## 🧪 Ejecutar Pruebas (Opcional)

```bash
pytest
```

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

El workflow se define en `.github/workflows/ci.yml`.

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
├── config.py                     # Configuración del proyecto
├── run.py                        # Punto de entrada de la aplicación
├── requirements.txt              # Dependencias del proyecto
├── .env                          # Variables de entorno (no versionar)
├── .env-template                 # Plantilla de variables de entorno
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
