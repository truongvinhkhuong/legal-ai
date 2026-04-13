"""Document and DocumentRelationship models — relational metadata for ingested documents."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.db.models.tenant import Tenant


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    doc_number: Mapped[str] = mapped_column(String(100), default="", index=True)
    doc_title: Mapped[str] = mapped_column(Text, default="")
    doc_type: Mapped[str] = mapped_column(String(50), default="khac", index=True)
    status: Mapped[str] = mapped_column(String(50), default="hieu_luc", index=True)
    issuing_authority: Mapped[str] = mapped_column(String(255), default="")
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    legal_hierarchy: Mapped[int] = mapped_column(Integer, default=5)
    access_level: Mapped[str] = mapped_column(String(50), default="public")
    allowed_departments: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: ["all"])
    scope: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: ["toan_cong_ty"])
    original_file_path: Mapped[str] = mapped_column(Text, default="")
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    structure_detected: Mapped[str] = mapped_column(String(50), default="")
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    tenant: Mapped[Tenant] = relationship(back_populates="documents")
    source_relationships: Mapped[list[DocumentRelationship]] = relationship(
        foreign_keys="DocumentRelationship.source_doc_id",
        back_populates="source_doc",
        cascade="all, delete-orphan",
    )
    target_relationships: Mapped[list[DocumentRelationship]] = relationship(
        foreign_keys="DocumentRelationship.target_doc_id",
        back_populates="target_doc",
        cascade="all, delete-orphan",
    )


class DocumentRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_relationships"

    source_doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    target_doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sua_doi|thay_the|huong_dan|bai_bo|dan_chieu
    notes: Mapped[str] = mapped_column(Text, default="")

    # Relationships
    source_doc: Mapped[Document] = relationship(
        foreign_keys=[source_doc_id], back_populates="source_relationships"
    )
    target_doc: Mapped[Document] = relationship(
        foreign_keys=[target_doc_id], back_populates="target_relationships"
    )
