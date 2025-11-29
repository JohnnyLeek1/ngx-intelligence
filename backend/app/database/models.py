"""
SQLAlchemy ORM models for ngx-intelligence.

Defines all database tables and relationships.
"""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses String(36).
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if isinstance(value, UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, UUID):
            return value
        return UUID(value)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    type_annotation_map = {
        UUID: GUID,
    }


class UserRole(str, enum.Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


class ProcessingStatus(str, enum.Enum):
    """Document processing status enumeration."""

    SUCCESS = "success"
    PENDING_APPROVAL = "pending_approval"
    FAILED = "failed"
    REJECTED = "rejected"


class QueueStatus(str, enum.Enum):
    """Processing queue status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalStatus(str, enum.Enum):
    """Approval queue status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.USER
    )
    paperless_url: Mapped[str] = mapped_column(String(255), nullable=False)
    paperless_username: Mapped[str] = mapped_column(String(255), nullable=False)
    paperless_token: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    processed_documents: Mapped[list["ProcessedDocument"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    approval_queue: Mapped[list["ApprovalQueue"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    processing_queue: Mapped[list["ProcessingQueue"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_corrections: Mapped[list["UserCorrection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class ProcessedDocument(Base):
    """Processed document tracking model."""

    __tablename__ = "processed_documents"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    paperless_document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus), nullable=False
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    suggested_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    applied_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reprocess_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="processed_documents")
    approval_queue_item: Mapped[Optional["ApprovalQueue"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    corrections: Mapped[list["UserCorrection"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProcessedDocument(id={self.id}, paperless_id={self.paperless_document_id}, status={self.status})>"


class ApprovalQueue(Base):
    """Approval queue model for pending document approvals."""

    __tablename__ = "approval_queue"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        GUID, ForeignKey("processed_documents.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    suggestions: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING
    )

    # Relationships
    document: Mapped["ProcessedDocument"] = relationship(back_populates="approval_queue_item")
    user: Mapped["User"] = relationship(back_populates="approval_queue")

    def __repr__(self) -> str:
        return f"<ApprovalQueue(id={self.id}, status={self.status})>"


class ExampleLibrary(Base):
    """Example library for AI learning."""

    __tablename__ = "example_library"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )  # NULL = global example
    paperless_document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    correspondent: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(255), nullable=False)
    tags: Mapped[list] = mapped_column(JSON, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    embedding: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # For future vector similarity

    # Relationships
    user: Mapped[Optional["User"]] = relationship()

    def __repr__(self) -> str:
        return f"<ExampleLibrary(id={self.id}, document_type={self.document_type})>"


class UserCorrection(Base):
    """User corrections for AI learning."""

    __tablename__ = "user_corrections"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(
        GUID, ForeignKey("processed_documents.id"), nullable=False
    )
    field: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'correspondent', 'type', 'tags', etc.
    original_value: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="user_corrections")
    document: Mapped["ProcessedDocument"] = relationship(back_populates="corrections")

    def __repr__(self) -> str:
        return f"<UserCorrection(id={self.id}, field={self.field})>"


class ProcessingQueue(Base):
    """Processing queue for document processing tasks."""

    __tablename__ = "processing_queue"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    paperless_document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # For future prioritization
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), nullable=False, default=QueueStatus.QUEUED
    )
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="processing_queue")

    def __repr__(self) -> str:
        return f"<ProcessingQueue(id={self.id}, status={self.status}, paperless_id={self.paperless_document_id})>"


class AIPrompt(Base):
    """AI prompt version history."""

    __tablename__ = "ai_prompts"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    prompt_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'system', 'classification', etc.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<AIPrompt(id={self.id}, type={self.prompt_type}, version={self.version})>"


class Setting(Base):
    """Application settings storage."""

    __tablename__ = "settings"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_by: Mapped[UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    updater: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<Setting(key={self.key})>"
