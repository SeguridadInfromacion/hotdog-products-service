"""Modelos de la base de datos (el esquema real vive en el repo hotdog-database)."""

import uuid
from datetime import datetime

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, UtcDateTime, utcnow


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    description: Mapped[str] = mapped_column(String(200), default="")
    price: Mapped[int]
    is_available: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    actor: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(48))
    target: Mapped[str] = mapped_column(String(120), default="")
    ip: Mapped[str] = mapped_column(String(45), default="")
