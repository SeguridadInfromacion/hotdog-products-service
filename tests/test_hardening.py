"""Entradas hostiles y fugas de información en products-service."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import ProductService
from tests.conftest import CSRF_HEADER

HOTDOG = {"name": "Perro Especial", "description": "Con queso y tocineta.", "price": 12000}


@pytest.mark.parametrize("field", ["name", "description"])
@pytest.mark.parametrize(
    "text", ["Perro\x00", "Perro\n2026-01-01 INFO audit actor='cajero'", "Perro\r\nX", "Perro\x7f"]
)
def test_control_characters_cannot_reach_the_database_or_forge_log_lines(admin_client, field, text):
    response = admin_client.post("/api/products", json={**HOTDOG, field: text})
    assert response.status_code == 422


def test_validation_errors_do_not_echo_the_request(admin_client):
    response = admin_client.post("/api/products", json={**HOTDOG, "price": "valor-enviado"})
    assert response.status_code == 422
    assert "valor-enviado" not in response.text


def test_unexpected_errors_are_generic_and_never_cached(admin_client, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("detalle interno que no debe salir")

    monkeypatch.setattr(ProductService, "list_products", explode)
    client = TestClient(
        create_app(),
        base_url="https://testserver",
        headers=CSRF_HEADER,
        raise_server_exceptions=False,
    )
    client.cookies.set("access_token", admin_client.cookies["access_token"])

    response = client.get("/api/products")

    assert response.status_code == 500
    assert "detalle interno" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_trailing_slash_does_not_redirect(admin_client):
    response = admin_client.get("/api/products/", follow_redirects=False)
    assert response.status_code == 404
