"""Tenant model — multi-tenancy root."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.db.models.document import Document
    from src.db.models.user import User


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free|starter|pro|enterprise
    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    users: Mapped[list[User]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    documents: Mapped[list[Document]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
