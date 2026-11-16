"""Rutas HTTP del menú. Leer: cualquier usuario con sesión. Modificar: solo admin."""

import uuid

from fastapi import APIRouter, status

from app.dependencies import AdminUser, ClientIp, CurrentUser, SessionDep
from app.repositories import AuditRepository
from app.schemas import AuditOut, ProductIn, ProductOut
from app.services import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    _: CurrentUser, session: SessionDep, only_available: bool = False
) -> list[ProductOut]:
    products = ProductService(session).list_products(only_available=only_available)
    return [ProductOut.model_validate(product) for product in products]


# Debe declararse antes de "/{product_id}" para que "audit" no se lea como un id.
@router.get("/audit", response_model=list[AuditOut])
def audit_trail(_: AdminUser, session: SessionDep) -> list[AuditOut]:
    return [AuditOut.model_validate(entry) for entry in AuditRepository(session).recent()]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, _: CurrentUser, session: SessionDep) -> ProductOut:
    return ProductOut.model_validate(ProductService(session).get_product(product_id))


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductIn, admin: AdminUser, session: SessionDep, ip: ClientIp
) -> ProductOut:
    product = ProductService(session).create_product(data, actor=admin.username, ip=ip)
    return ProductOut.model_validate(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: uuid.UUID, data: ProductIn, admin: AdminUser, session: SessionDep, ip: ClientIp
) -> ProductOut:
    product = ProductService(session).update_product(product_id, data, actor=admin.username, ip=ip)
    return ProductOut.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: uuid.UUID, admin: AdminUser, session: SessionDep, ip: ClientIp
) -> None:
    ProductService(session).delete_product(product_id, actor=admin.username, ip=ip)
