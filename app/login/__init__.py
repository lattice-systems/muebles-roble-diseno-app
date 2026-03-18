"""
Módulo de login

Este módulo se encarga de gestionar las rutas y funcionalidades relacionadas con el inicio de sesión de los usuarios.
Aquí se definen las rutas para mostrar el formulario de login, procesar las credenciales ingresadas por el usuario
y manejar la autenticación.
"""

from flask import Blueprint

login_bp = Blueprint("login", __name__)

from . import routes  # noqa: E402, F401
