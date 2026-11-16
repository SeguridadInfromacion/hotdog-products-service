"""Configuración del servicio, leída únicamente de variables de entorno."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str
    # Este servicio solo tiene la llave PÚBLICA: puede verificar tokens, no crearlos.
    jwt_public_key_file: Path
    jwt_issuer: str = "hotdog-auth"
    jwt_audience: str = "hotdog-api"

    # La documentación interactiva queda apagada salvo que se pida explícitamente.
    enable_docs: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
