"""Casos de uso del menú: listar, crear, editar y eliminar productos."""

import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import Conflict, NotFound
from app.models import Product
from app.repositories import AuditRepository, ProductRepository
from app.schemas import ProductIn

DUPLICATE_NAME = "Ya hay un producto con ese nombre."


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._products = ProductRepository(session)
        self._audit = AuditRepository(session)

    def list_products(self, *, only_available: bool = False) -> Sequence[Product]:
        return self._products.list_all(only_available=only_available)

    def get_product(self, product_id: uuid.UUID) -> Product:
        product = self._products.get(product_id)
        if product is None:
            raise NotFound("Ese producto no existe.")
        return product

    def create_product(self, data: ProductIn, *, actor: str, ip: str) -> Product:
        product = Product(**data.model_dump())
        try:
            self._products.add(product)
        except IntegrityError as error:
            self._session.rollback()
            raise Conflict(DUPLICATE_NAME) from error
        self._audit.record(actor=actor, action="producto.crear", target=product.name, ip=ip)
        self._session.commit()
        return product

    def update_product(
        self, product_id: uuid.UUID, data: ProductIn, *, actor: str, ip: str
    ) -> Product:
        product = self.get_product(product_id)
        for field, value in data.model_dump().items():
            setattr(product, field, value)
        try:
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise Conflict(DUPLICATE_NAME) from error
        self._audit.record(actor=actor, action="producto.editar", target=product.name, ip=ip)
        self._session.commit()
        return product

    def delete_product(self, product_id: uuid.UUID, *, actor: str, ip: str) -> None:
        product = self.get_product(product_id)
        self._products.delete(product)
        self._audit.record(actor=actor, action="producto.eliminar", target=product.name, ip=ip)
        self._session.commit()
