"""Contract and ContractTemplate models for AI contract drafting."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.db.models.tenant import Tenant


class ContractTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata for contract templates. Actual template content is in Jinja2 files."""

    __tablename__ = "contract_templates"

    template_key: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    description_vi: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # lao_dong, thue, dich_vu
    version: Mapped[int] = mapped_column(Integer, default=1)
    required_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    compliance_rule_ids: Mapped[list] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    contracts: Mapped[list[Contract]] = relationship(back_populates="template")


class Contract(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-created contracts from templates."""

    __tablename__ = "contracts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contract_templates.id"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(
        String(20), default="draft", index=True
    )  # draft, review, final
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    rendered_content: Mapped[str] = mapped_column(Text, default="")
    compliance_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    template: Mapped[ContractTemplate] = relationship(back_populates="contracts")
