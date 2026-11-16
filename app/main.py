"""Punto de entrada del servicio de productos."""

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import require_csrf_header
from app.errors import AppError
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("products-service")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="hotdog-products-service",
        dependencies=[Depends(require_csrf_header)],
        # Sin redirecciones automáticas de "/ruta/" a "/ruta": se arman con la
        # cabecera Host del cliente y no aportan nada a esta API.
        redirect_slashes=False,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    app.include_router(router)

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.middleware("http")
    async def never_cache_api_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, error: AppError) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        # Se dice dónde y por qué falló, pero nunca se devuelve el valor recibido:
        # podría ser una contraseña y terminaría en logs o capturas del navegador.
        issues = [{"loc": list(issue["loc"]), "msg": issue["msg"]} for issue in error.errors()]
        return JSONResponse(status_code=422, content={"detail": issues})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, error: Exception) -> JSONResponse:
        # El detalle va al log del servidor; al cliente nunca se le muestran trazas.
        logger.exception("Error no controlado", exc_info=error)
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error interno."},
            headers={"Cache-Control": "no-store"},
        )

    return app
