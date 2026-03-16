# 📋 Convenciones de Código

Este documento establece las convenciones de código para el proyecto **Backend Furniture Store**.

---

## 📝 Estilo de Código

### Python Style Guide

Seguimos **PEP 8** como guía base de estilo. Utilizamos **Black** como formateador automático.

```bash
# Formatear código
black .

# Verificar estilo sin modificar
black --check .
```

### Configuración de Black

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ["py310"]
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | node_modules
  | migrations
  | build
  | dist
  | __pycache__
)/
'''
```

**Nota:** Line-length es **88 caracteres** (no 100). Ver [DEVELOPMENT_TOOLS.md](DEVELOPMENT_TOOLS.md) para más detalles.

---

## 📁 Convenciones de Nombres

### Archivos y Carpetas

| Tipo           | Convención | Ejemplo           |
|----------------|------------|-------------------|
| Módulos Python | snake_case | `user_service.py` |
| Carpetas       | snake_case | `wood_types/`     |
| Clases         | PascalCase | `ColorService`    |

### Variables y Funciones

| Tipo             | Convención       | Ejemplo             |
|------------------|------------------|---------------------|
| Variables        | snake_case       | `user_name`         |
| Funciones        | snake_case       | `get_all_colors()`  |
| Constantes       | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE`     |
| Clases           | PascalCase       | `ColorModel`        |
| Métodos privados | _snake_case      | `_validate_input()` |

### Modelos de Base de Datos

```python
class Color(db.Model):
    """
    Modelo de Color para el catálogo.
    
    Attributes:
        id: Identificador único
        name: Nombre del color
        hex_code: Código hexadecimal del color
        is_active: Estado activo/inactivo
    """
    __tablename__ = 'colors'  # Plural, snake_case

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    hex_code = db.Column(db.String(7), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
```

---

## 🏗️ Estructura de Módulos

### Estructura de un Módulo de Dominio

```
catalogs/
└── colors/
    ├── __init__.py      # Blueprint y exports
    ├── routes.py        # Rutas y controladores
    ├── services.py      # Lógica de negocio
    └── forms.py         # Formularios con WTForms

templates/
└── colors/
    └── create.html      # Formulario de creación
```

### Contenido de `__init__.py`

```python
"""
Módulo de gestión de colores.

Proporciona endpoints para CRUD de colores del catálogo.
"""

from flask import Blueprint

colors_bp = Blueprint('colors', __name__)

from . import routes  # noqa: E402, F401
```

### Contenido de `routes.py`

```python
"""
Rutas/Controladores para el módulo de colores.
"""

from flask import flash, redirect, render_template, url_for

from . import colors_bp
from .forms import ColorForm
from .services import ColorService
from app.exceptions import ConflictError


@colors_bp.route('/create', methods=['GET', 'POST'])
def create_color():
    """
    Muestra el formulario y crea un nuevo color.
    
    GET: Renderiza el formulario de creación.
    POST: Valida el formulario, crea el color y redirige.
    
    Returns:
        GET - HTML: Página con el formulario
        POST - Redirect: Redirige con mensaje flash
    """
    form = ColorForm()

    if form.validate_on_submit():
        data = {'name': form.name.data}
        try:
            ColorService.create(data)
            flash('Color creado exitosamente', 'success')
            return redirect(url_for('colors.create_color'))
        except ConflictError as e:
            flash(e.message, 'error')

    return render_template('colors/create.html', form=form)
```

### Contenido de `forms.py`

```python
"""
Formularios para el módulo de colores.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class ColorForm(FlaskForm):
    """Formulario para crear un color."""

    name = StringField(
        'Nombre',
        validators=[
            DataRequired(message='El nombre del color es requerido'),
            Length(max=50, message='El nombre no puede exceder 50 caracteres'),
        ],
    )
```

### Contenido de `services.py`

```python
"""
Servicios de lógica de negocio para colores.
"""

from app.models.color import Color
from app.extensions import db
from app.exceptions import ConflictError, ValidationError


class ColorService:
    """Servicio para operaciones de negocio relacionadas con colores."""

    @staticmethod
    def create(data: dict) -> dict:
        """
        Crea un nuevo color.
        
        Args:
            data: Diccionario con los datos del color
            
        Returns:
            dict: Color creado serializado
            
        Raises:
            ValidationError: Si el nombre está vacío
            ConflictError: Si el color ya existe
        """
        name = data.get('name')
        if not name or not name.strip():
            raise ValidationError('El nombre del color es requerido')

        existing = Color.query.filter_by(name=name.strip()).first()
        if existing:
            raise ConflictError(f"Ya existe un color con el nombre '{name}'")

        color = Color(name=name.strip())
        db.session.add(color)
        db.session.commit()
        return color.to_dict()
```

---

## 📚 Documentación

### Docstrings

Utilizamos el formato **Google Style** para docstrings:

```python
from typing import Optional

def create_color(name: str, hex_code: Optional[str] = None) -> dict:
    """
    Crea un nuevo color en el catálogo.
    
    Args:
        name: Nombre del color (requerido)
        hex_code: Código hexadecimal del color (opcional)
        
    Returns:
        dict: Color creado serializado
        
    Raises:
        ValidationError: Si el nombre está vacío
        ConflictError: Si el color ya existe
        
    Example:
        >>> create_color("Rojo", "#FF0000")
        {'id': 1, 'name': 'Rojo', 'hex_code': '#FF0000'}
    """
    pass
```

### Type Hints

Usar type hints en todas las funciones:

```python
from typing import List, Optional, Dict, Any


def get_colors_by_status(is_active: bool = True) -> List[Dict[str, Any]]:
    """Obtiene colores filtrados por estado."""
    pass


def find_color(color_id: int) -> Optional[Color]:
    """Busca un color, retorna None si no existe."""
    pass
```

---

## 🌐 Convenciones de Rutas y Vistas

### URLs

| Acción     | Método | URL                       | Ejemplo            |
|------------|--------|---------------------------|--------------------|   
| Listar     | GET    | `/{recurso}/`             | `/colors/`         |
| Crear      | POST   | `/{recurso}/`             | `/colors/`         |
| Detalle    | GET    | `/{recurso}/{id}`         | `/colors/1`        |
| Editar     | POST   | `/{recurso}/{id}/edit`    | `/colors/1/edit`   |
| Eliminar   | POST   | `/{recurso}/{id}/delete`  | `/colors/1/delete` |

### Templates Jinja2

#### Template Base (`base.html`)

Todos los templates extienden de `base.html` que contiene:
- Estructura HTML común
- Navegación
- Bloque de mensajes flash
- Bloque `content` para contenido específico

```html
{%- raw %}
{% extends "base.html" %}
{% block title %}Título - Furniture Store{% endblock %}
{% block content %}
    <!-- Contenido específico -->
{% endblock %}
{%- endraw %}
```

#### Organización de Templates

```
templates/
├── base.html              # Layout base
└── colors/                # Templates por módulo
    └── list.html          # Listado + formulario
```

#### Mensajes Flash

Se usa `flash()` para retroalimentación al usuario:

```python
# En routes.py
flash('Color creado exitosamente', 'success')  # Mensaje de éxito
flash(e.message, 'error')                      # Mensaje de error
```

#### Patrón PRG (Post/Redirect/Get)

Después de un POST exitoso, siempre redirigir:

```python
return redirect(url_for('colors.create_color'))
```

---

## 🔢 Códigos HTTP

| Código | Uso                                        |
|--------|--------------------------------------------|
| 200    | OK - Operación exitosa                     |
| 201    | Created - Recurso creado                   |
| 204    | No Content - Eliminación exitosa           |
| 400    | Bad Request - Error de validación          |
| 401    | Unauthorized - No autenticado              |
| 403    | Forbidden - Sin permisos                   |
| 404    | Not Found - Recurso no encontrado          |
| 409    | Conflict - Conflicto (duplicado)           |
| 422    | Unprocessable Entity - Error de negocio    |
| 500    | Internal Server Error - Error del servidor |

---

## 🧪 Convenciones de Testing

### Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidos
├── test_config.py           # Tests de configuración
└── catalogs/
    └── test_colors.py       # Tests del módulo colors
```

### Nomenclatura de Tests

```python
def test_create_color_form_renders_template():
    """Test: GET /colors/create renderiza el formulario."""
    pass


def test_create_color_with_valid_data_redirects():
    """Test: POST /colors/create con datos válidos redirige."""
    pass


def test_create_color_with_empty_name_shows_form_error():
    """Test: POST /colors/create sin nombre muestra error del formulario."""
    pass


def test_create_color_duplicate_shows_error_flash():
    """Test: POST /colors/create con nombre duplicado muestra flash de error."""
    pass
```

---

## 📦 Imports

### Orden de Imports

1. Librerías estándar de Python
2. Librerías de terceros
3. Imports locales de la aplicación

```python
# 1. Librerías estándar
from datetime import datetime
from typing import List, Optional

# 2. Librerías de terceros
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from sqlalchemy import or_, and_

# 3. Imports locales
from app.extensions import db, csrf
from app.models.color import Color
from app.exceptions import ConflictError
```

---

## ✅ Checklist de Revisión de Código

- [ ] El código sigue PEP 8 (formateado con Black)
- [ ] Todas las funciones tienen docstrings
- [ ] Se usan type hints
- [ ] Los nombres son descriptivos y siguen las convenciones
- [ ] Las excepciones se manejan correctamente
- [ ] Los formularios usan `FlaskForm` con validadores
- [ ] Los templates incluyen `form.hidden_tag()` para CSRF
- [ ] Los templates muestran errores de formulario
- [ ] Se aplica el patrón PRG después de POST
- [ ] No hay código comentado innecesario
- [ ] Los imports están ordenados correctamente

---

## 🛠️ Herramientas de Calidad

El proyecto incluye herramientas automatizadas que se ejecutan localmente y en CI/CD:

### Herramientas Locales

| Herramienta | Comando | Descripción |
|-------------|---------|-------------|
| **Black** | `black .` | Formatea código Python automáticamente |
| **Ruff** | `ruff check .` | Linting rápido de Python |
| **Mypy** | `mypy app/` | Type checking estático |
| **djLint** | `djlint app/templates/ --lint` | Linting de templates HTML/Jinja2 |

### Pre-commit Hooks

Para ejecutar estos checks automáticamente antes de hacer commit:

```bash
pre-commit install
```

### CI/CD en GitHub Actions

El proyecto ejecuta automáticamente todos los checks en cada push/PR a `main` o `dev`.

Ver [DEVELOPMENT_TOOLS.md](DEVELOPMENT_TOOLS.md) para configuración completa y solución de problemas.

