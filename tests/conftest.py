"""Entorno de pruebas: llaves RSA temporales y base SQLite en memoria.

Los tokens se firman aquí con una llave privada de prueba, igual que lo haría
auth-service; el servicio bajo prueba solo conoce la llave pública.
"""

import os
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _key.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
)
_public_path = Path(tempfile.mkdtemp(prefix="hotdog-keys-")) / "public.pem"
_public_path.write_bytes(
    _key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
)
os.environ.update(
    DATABASE_URL="sqlite+pysqlite:///:memory:",
    JWT_PUBLIC_KEY_FILE=str(_public_path),
)

# Los imports de la app van después de preparar el entorno.
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}


def make_token(role: str = "admin", username: str = "admin", **overrides) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid4()),
        "username": username,
        "role": role,
        "iss": "hotdog-auth",
        "aud": "hotdog-api",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **overrides,
    }
    return jwt.encode(claims, PRIVATE_PEM, algorithm="RS256")


def _client_with(token: str | None) -> TestClient:
    client = TestClient(create_app(), base_url="https://testserver", headers=CSRF_HEADER)
    if token:
        client.cookies.set("access_token", token)
    return client


@pytest.fixture(autouse=True)
def _fresh_database():
    Base.metadata.drop_all(get_engine())
    Base.metadata.create_all(get_engine())
    yield


@pytest.fixture
def anonymous_client():
    return _client_with(None)


@pytest.fixture
def admin_client():
    return _client_with(make_token("admin", "admin"))


@pytest.fixture
def cashier_client():
    return _client_with(make_token("cashier", "cajero"))
