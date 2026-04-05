"""
Módulo de excepciones personalizadas para el manejo centralizado de errores.

Este módulo define excepciones específicas del dominio de negocio
que permiten un manejo consistente de errores en toda la aplicación.
"""

from typing import Optional
from flask import jsonify, render_template, request


class AppException(Exception):
    """Excepción base de la aplicación."""

    def __init__(
        self, message: str, status_code: int = 500, payload: Optional[dict] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> dict:
        """Convierte la excepción a un diccionario para la respuesta JSON."""
        response = {
            "success": False,
            "error": {"message": self.message, "code": self.status_code},
        }
        if self.payload:
            response["error"]["details"] = self.payload
        return response


class ValidationError(AppException):
    """Excepción para errores de validación de datos de entrada."""

    def __init__(
        self,
        message: str = "Datos de entrada inválidos",
        payload: Optional[dict] = None,
    ):
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(AppException):
    """Excepción para recursos no encontrados."""

    def __init__(
        self, message: str = "Recurso no encontrado", payload: Optional[dict] = None
    ):
        super().__init__(message, status_code=404, payload=payload)


class ConflictError(AppException):
    """Excepción para conflictos de datos (ej: duplicados)."""

    def __init__(
        self,
        message: str = "Conflicto con el recurso existente",
        payload: Optional[dict] = None,
    ):
        super().__init__(message, status_code=409, payload=payload)


class UnauthorizedError(AppException):
    """Excepción para accesos no autenticados."""

    def __init__(self, message: str = "No autenticado", payload: Optional[dict] = None):
        super().__init__(message, status_code=401, payload=payload)


class ForbiddenError(AppException):
    """Excepción para accesos sin permiso suficiente."""

    def __init__(
        self,
        message: str = "Sin permisos para acceder a este recurso",
        payload: Optional[dict] = None,
    ):
        super().__init__(message, status_code=403, payload=payload)


def register_error_handlers(app):
    """
    Registra los manejadores de errores globales en la aplicación Flask.

    Args:
        app: Instancia de la aplicación Flask
    """

    @app.errorhandler(AppException)
    def handle_app_exception(error):
        """Manejador para excepciones personalizadas de la aplicación."""
        app.logger.error(f"AppException: {error.message}")

        wants_json = request.is_json or (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        )
        if wants_json:
            return jsonify(error.to_dict()), error.status_code

        return (
            render_template(
                "errors/error.html",
                code=error.status_code,
                message=error.message,
            ),
            error.status_code,
        )

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Manejador para errores 400 Bad Request."""
        return (
            render_template(
                "errors/error.html",
                code=400,
                message="Solicitud incorrecta",
            ),
            400,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        """Manejador para errores 404 Not Found."""
        return (
            render_template(
                "errors/error.html",
                code=404,
                message="Página no encontrada",
            ),
            404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Manejador para errores 405 Method Not Allowed."""
        return (
            render_template(
                "errors/error.html",
                code=405,
                message="Método no permitido",
            ),
            405,
        )

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Manejador para errores 403 Forbidden."""
        wants_json = request.is_json or (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        )
        if wants_json:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "message": "Sin permisos para acceder a este recurso",
                            "code": 403,
                        },
                    }
                ),
                403,
            )

        return (
            render_template(
                "errors/error.html",
                code=403,
                message="Sin permisos para acceder a este recurso",
            ),
            403,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Manejador para errores 500 Internal Server Error."""
        app.logger.error(f"500 Error: {error}")
        return (
            render_template(
                "errors/error.html",
                code=500,
                message="Error interno del servidor",
            ),
            500,
        )
