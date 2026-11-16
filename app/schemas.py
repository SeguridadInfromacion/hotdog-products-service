"""Contratos de entrada y salida de la API. Toda entrada se valida aquí."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MIN_PRICE = 100
MAX_PRICE = 1_000_000

# Sin caracteres de control (saltos de línea, NUL...): no sirven en un nombre y
# permitirían falsificar líneas del log o provocar errores en la base.
PRINTABLE = r"^[^\x00-\x1f\x7f]*$"

ProductName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60, pattern=PRINTABLE)
]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=200, pattern=PRINTABLE)
]


class ProductIn(BaseModel):
    """Datos para crear o reemplazar un producto."""

    # Rechaza campos desconocidos: evita la asignación masiva de atributos.
    model_config = ConfigDict(extra="forbid")

    name: ProductName
    description: Description = ""
    price: int = Field(ge=MIN_PRICE, le=MAX_PRICE, strict=True)
    is_available: bool = True


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    price: int
    is_available: bool
    updated_at: datetime


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    occurred_at: datetime
    actor: str
    action: str
    target: str
    ip: str
