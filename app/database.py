"""Conexión a la base de datos y sesión por petición."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import DateTime, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from app.config import get_settings


class Base(DeclarativeBase):
    """Base de todos los modelos."""


class UtcDateTime(TypeDecorator):
    """Fecha y hora que siempre vuelve con zona horaria UTC, sin importar el motor."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


def utcnow() -> datetime:
    return datetime.now(UTC)


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if url.startswith("sqlite"):
        # Solo para pruebas: una única conexión en memoria compartida.
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Abre una sesión y garantiza que se cierre. El commit lo decide cada caso de uso."""
    session = _session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición."""
    with session_scope() as session:
        yield session
