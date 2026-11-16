"""Acceso a datos. Todas las consultas usan el ORM, que envía los valores
como parámetros: no hay SQL armado con texto del usuario (sin inyección SQL)."""

import logging
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Product

audit_logger = logging.getLogger("audit")


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, product_id: uuid.UUID) -> Product | None:
        return self._session.get(Product, product_id)

    def list_all(self, *, only_available: bool = False) -> Sequence[Product]:
        query = select(Product).order_by(Product.price, Product.name)
        if only_available:
            query = query.where(Product.is_available.is_(True))
        return self._session.scalars(query).all()

    def add(self, product: Product) -> Product:
        self._session.add(product)
        self._session.flush()
        return product

    def delete(self, product: Product) -> None:
        self._session.delete(product)


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, *, actor: str, action: str, target: str = "", ip: str = "") -> None:
        self._session.add(AuditLog(actor=actor, action=action, target=target[:120], ip=ip[:45]))
        # %r: un salto de línea en un dato no puede falsificar otra línea del log.
        audit_logger.info("actor=%r action=%r target=%r ip=%r", actor, action, target, ip)

    def recent(self, limit: int = 100) -> Sequence[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit)
        return self._session.scalars(query).all()
