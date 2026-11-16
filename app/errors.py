"""Errores de negocio. main.py los traduce a respuestas HTTP."""


class AppError(Exception):
    status_code = 400
    detail = "Solicitud inválida."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class NotAuthenticated(AppError):
    status_code = 401
    detail = "Debes iniciar sesión."


class PermissionDenied(AppError):
    status_code = 403
    detail = "No tienes permiso para hacer esto."


class NotFound(AppError):
    status_code = 404
    detail = "No encontrado."


class Conflict(AppError):
    status_code = 409
    detail = "Ya existe."


class Unprocessable(AppError):
    status_code = 422
    detail = "No se puede procesar la solicitud."


class ServiceUnavailable(AppError):
    status_code = 503
    detail = "Un servicio del que dependemos no está disponible."
