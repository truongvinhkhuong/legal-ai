"""User model — authentication and authorization."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.db.models.tenant import Tenant


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(50), default="viewer")  # admin|editor|viewer
    departments: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    access_levels: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=lambda: ["public"]
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    tenant: Mapped[Tenant] = relationship(back_populates="users")
