# 🛠️ Herramientas de Desarrollo y Calidad de Código

Este documento describe las herramientas de desarrollo integradas en el proyecto para mantener la calidad, consistencia y seguridad del código.

## 📋 Visión General

El proyecto utiliza un conjunto de herramientas automatizadas para:

- ✅ **Formateo consistente** de código Python y HTML/Jinja2
- ✅ **Linting** para detectar errores y problemas
- ✅ **Type checking** para verificar tipos estáticos
- ✅ **Seguridad** mediante análisis de vulnerabilidades
- ✅ **Automatización** mediante CI/CD en GitHub Actions

## 🔧 Herramientas Instaladas

### Python & Code Quality

| Herramienta    | Versión | Propósito                           | Comando                  |
|----------------|---------|-------------------------------------|--------------------------|
| **Black**      | 26.3.1  | Formateador de código Python        | `black .`                |
| **Ruff**       | 0.15.6  | Linter rápido para Python           | `ruff check .`           |
| **Mypy**       | 1.19.1  | Verificador de tipos estático       | `mypy app/`              |
| **Bandit**     | —       | Análisis de seguridad Python        | `bandit -r app/ -ll`     |

### Template & HTML Quality

| Herramienta    | Versión | Propósito                           | Comando                          |
|----------------|---------|-------------------------------------|----------------------------------|
| **djLint**     | 1.36.4  | Linter y formateador de Jinja2/HTML| `djlint app/templates/ --lint`   |

### Git Hooks

| Herramienta    | Versión | Propósito                           |
|----------------|---------|-------------------------------------|
| **Pre-commit** | 4.5.1   | Ejecuta checks antes de commits     |

## 📖 Configuración Local

### Archivos de Configuración

```
├── pyproject.toml           # Config Black y Ruff
├── mypy.ini                 # Config Mypy (type checking)
├── .djlintrc                # Config djLint
├── .editorconfig            # Config para IDEs
├── .pre-commit-config.yaml  # Config pre-commit hooks
└── .github/
    └── workflows/
        └── ci.yml           # GitHub Actions CI/CD
```

## 🚀 Uso Local

### Antes de Hacer Commit

Ejecuta los siguientes comandos para validar tu código:

```bash
# 1. Formatear código Python
black .

# 2. Verificar linting Python
ruff check .

# 3. Verificar tipos
mypy app/ --config-file=mypy.ini

# 4. Linting de templates
djlint app/templates/ --lint

# 5. Formatear templates
djlint app/templates/ --reformat
```

### O Instalar Pre-commit Hooks

Para ejecutar automáticamente estos checks antes de cada commit:

```bash
# Instalar hooks (una sola vez)
pre-commit install

# Los checks se ejecutarán automáticamente en git commit
# Puedes saltarlos si es necesario con:
git commit --no-verify
```

## 🤖 CI/CD Automático (GitHub Actions)

El proyecto ejecuta automáticamente todos los checks en:

- ✅ **Push** a `main` o `dev`
- ✅ **Pull Requests** a `main` o `dev`

### Workflow: `.github/workflows/ci.yml`

El workflow ejecuta 3 jobs en paralelo:

#### 1. **Quality Checks** (Requerido - debe pasar)
   - Black: Verifica formateo
   - Ruff: Linting rápido
   - Mypy: Type checking
   - djLint: Linting de templates

#### 2. **Security Checks** (Informativo)
   - Bandit: Análisis de seguridad Python

#### 3. **Summary** (Requerido - depende de Quality Checks)
   - Resumen final del workflow

### Ver Resultados

En GitHub:
1. Ve a la pestaña **Actions**
2. Selecciona el workflow **"CI - Linting, Formatting & Type Checks"**
3. Haz clic en el run que corresponda
4. Revisa los detalles de cada job

### Descargar Reportes

El workflow genera automáticamente reportes que se guardan como **Artifacts** por 30 días:

#### Quality Reports (Calidad de Código)
- `black-report.txt` - Resultados de Black
- `ruff-report.json` - Reporte detallado de Ruff
- `mypy-report.txt` - Resultados de Mypy
- `djlint-lint-report.txt` - Linting de templates
- `djlint-check-report.txt` - Formateo de templates

#### Security Reports (Seguridad)
- `bandit-report.json` - Análisis de seguridad Python

**Cómo descargar:**
1. En la página del workflow run
2. Baja hasta **"Artifacts"**
3. Haz clic en el artifact que necesites
4. Se descargará automáticamente

## ⚙️ Configuración Específica

### Black (Formateador Python)

**Archivo:** `pyproject.toml`

```toml
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

- **Line length:** 88 caracteres
- **Target:** Python 3.10
- **Exclusiones:** venv, migrations, node_modules, etc.

### Ruff (Linter Python)

**Archivo:** `pyproject.toml`

```toml
[tool.ruff]
exclude = [
    "migrations",
    "build",
    "venv",
    "node_modules",
    ".git",
    "dist",
    "__pycache__",
]
```

- Reglas estándar de PEP 8 y más
- Exclusiones: migraciones, venv, etc.

### Mypy (Type Checking)

**Archivo:** `mypy.ini`

```ini
[mypy]
python_version = 3.10
ignore_missing_imports = True

[mypy-migrations.*]
ignore_errors = True

[mypy-app.extensions]
ignore_errors = True

[mypy-app.models.*]
ignore_errors = True

[mypy-app.catalogs.*]
ignore_errors = True
```

- **Python 3.10** como target
- **Ignora módulos sin tipos** (DTOs, etc.)
- **Excepciones para áreas legadas** (models, catalogs)

### djLint (HTML/Jinja2 Linter)

**Archivo:** `.djlintrc`

Configuración estándar para Jinja2 con HTML5.

## 📊 Ejemplo: Flujo de Trabajo

```
1. Desarrollas código
2. Antes de commit:
   ├─ Pre-commit hooks se ejecutan (si están instalados)
   ├─ Black formatea el código
   ├─ Ruff valida linting
   ├─ Mypy verifica tipos
   └─ djLint valida templates

3. Si todo pasa: ✅ Commit exitoso

4. Si algo falla: ❌ Commit rechazado
   └─ Revisa los errores, corrígelos y vuelve a intentar

5. Haces push a GitHub

6. GitHub Actions:
   ├─ Ejecuta los mismos checks
   ├─ Ejecuta análisis de seguridad
   └─ Muestra resultados en el PR
```

## 🚨 Solución de Problemas

### Black rechaza mi formato

Black es opinionado. Si desacuerdas con su formato:

```bash
# Aplica el formato de Black
black .
```

Luego revisa los cambios y contribuye a la discusión del equipo.

### Mypy dice que hay errores de tipo

Primero, intenta resolver los errores manualmente. Si no es posible:

```bash
# Ignora un error específico (último recurso)
x = some_function()  # type: ignore
```

### djLint rechaza el template

Aplica el formato automático:

```bash
djlint app/templates/ --reformat
```

### Pre-commit hooks no se ejecutan

```bash
# Reinstala los hooks
pre-commit uninstall
pre-commit install
```

## 📚 Referencias

- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [djLint Documentation](https://www.djlint.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🔗 Documentos Relacionados

- [CODING_CONVENTIONS.md](CODING_CONVENTIONS.md) - Convenciones de código
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura del proyecto
- [README.md](../README.md) - Guía de inicio rápido
