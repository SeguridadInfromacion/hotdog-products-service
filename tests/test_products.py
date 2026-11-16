"""CRUD del menú, validación de entradas y control de acceso."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.conftest import make_token

HOTDOG = {"name": "Perro Especial", "description": "Con queso y tocineta.", "price": 12000}


def _create(client, **overrides):
    return client.post("/api/products", json={**HOTDOG, **overrides})


# --- CRUD --------------------------------------------------------------------


def test_admin_creates_and_lists_a_product(admin_client):
    created = _create(admin_client)

    assert created.status_code == 201
    assert created.json()["is_available"] is True
    names = [product["name"] for product in admin_client.get("/api/products").json()]
    assert names == ["Perro Especial"]


def test_admin_updates_a_product(admin_client):
    product_id = _create(admin_client).json()["id"]

    updated = admin_client.put(
        f"/api/products/{product_id}", json={**HOTDOG, "price": 13500, "is_available": False}
    )

    assert updated.status_code == 200
    assert updated.json()["price"] == 13500
    assert updated.json()["is_available"] is False


def test_admin_deletes_a_product(admin_client):
    product_id = _create(admin_client).json()["id"]

    assert admin_client.delete(f"/api/products/{product_id}").status_code == 204
    assert admin_client.get(f"/api/products/{product_id}").status_code == 404


def test_only_available_filter_hides_sold_out_products(admin_client):
    _create(admin_client)
    _create(admin_client, name="Perro Agotado", is_available=False)

    names = [p["name"] for p in admin_client.get("/api/products?only_available=true").json()]

    assert names == ["Perro Especial"]


def test_duplicate_name_is_a_conflict(admin_client):
    assert _create(admin_client).status_code == 201
    assert _create(admin_client).status_code == 409


def test_unknown_product_is_404(admin_client):
    assert admin_client.get(f"/api/products/{uuid.uuid4()}").status_code == 404
    assert admin_client.put(f"/api/products/{uuid.uuid4()}", json=HOTDOG).status_code == 404
    assert admin_client.delete(f"/api/products/{uuid.uuid4()}").status_code == 404


# --- Validación de entradas --------------------------------------------------


@pytest.mark.parametrize(
    "bad_fields",
    [
        {"price": 0},
        {"price": -5000},
        {"price": 99_999_999},
        {"price": "12000"},
        {"price": 12000.5},
        {"name": ""},
        {"name": "x" * 61},
        {"description": "x" * 201},
        {"id": str(uuid.uuid4())},
        {"created_at": "2020-01-01T00:00:00Z"},
    ],
)
def test_invalid_input_is_rejected(admin_client, bad_fields):
    assert _create(admin_client, **bad_fields).status_code == 422


def test_sql_injection_text_is_stored_as_plain_text(admin_client):
    malicious = "x'); DROP TABLE products; --"

    created = _create(admin_client, name=malicious)

    assert created.status_code == 201
    assert created.json()["name"] == malicious
    assert len(admin_client.get("/api/products").json()) == 1


def test_malformed_id_is_rejected_before_reaching_the_database(admin_client):
    assert admin_client.get("/api/products/1 OR 1=1").status_code == 422


# --- Control de acceso -------------------------------------------------------


def test_anonymous_cannot_read_or_write(anonymous_client):
    assert anonymous_client.get("/api/products").status_code == 401
    assert _create(anonymous_client).status_code == 401


def test_cashier_can_read_but_not_modify(admin_client, cashier_client):
    product_id = _create(admin_client).json()["id"]

    assert cashier_client.get("/api/products").status_code == 200
    assert _create(cashier_client, name="Otro").status_code == 403
    assert cashier_client.put(f"/api/products/{product_id}", json=HOTDOG).status_code == 403
    assert cashier_client.delete(f"/api/products/{product_id}").status_code == 403
    assert cashier_client.get("/api/products/audit").status_code == 403


def test_writes_need_the_csrf_header(admin_client):
    response = admin_client.post("/api/products", json=HOTDOG, headers={"X-Requested-With": ""})
    assert response.status_code == 403


def test_token_signed_by_someone_else_is_rejected(anonymous_client):
    attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = attacker_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    now = datetime.now(UTC)
    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "username": "admin",
            "role": "admin",
            "iss": "hotdog-auth",
            "aud": "hotdog-api",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        pem,
        algorithm="RS256",
    )
    anonymous_client.cookies.set("access_token", forged)
    assert anonymous_client.get("/api/products").status_code == 401


def test_expired_token_is_rejected(anonymous_client):
    expired = make_token(exp=datetime.now(UTC) - timedelta(minutes=1))
    anonymous_client.cookies.set("access_token", expired)
    assert anonymous_client.get("/api/products").status_code == 401


def test_token_without_role_claim_is_rejected(anonymous_client):
    token = make_token()
    claims = jwt.decode(token, options={"verify_signature": False})
    del claims["role"]
    from tests.conftest import PRIVATE_PEM

    anonymous_client.cookies.set("access_token", jwt.encode(claims, PRIVATE_PEM, algorithm="RS256"))
    assert anonymous_client.get("/api/products").status_code == 401


# --- Auditoría ---------------------------------------------------------------


def test_every_change_is_audited_with_the_actor(admin_client):
    product_id = _create(admin_client).json()["id"]
    admin_client.put(f"/api/products/{product_id}", json={**HOTDOG, "price": 9000})
    admin_client.delete(f"/api/products/{product_id}")

    trail = admin_client.get("/api/products/audit").json()

    assert {entry["action"] for entry in trail} == {
        "producto.crear",
        "producto.editar",
        "producto.eliminar",
    }
    assert {entry["actor"] for entry in trail} == {"admin"}
