import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .db.postgres import Base


class ReportStatus(str, Enum):
    PENDING = "P"
    FAILED = "F"
    GENERATED = "G"
    DELETED = "D"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    is_admin = Column(Boolean, nullable=False, default=False)


class Report(Base):
    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    hash_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    template_id = Column(String(100), nullable=False, index=True)
    input_args = Column(JSONB, nullable=False, default=dict)
    status = Column(SAEnum(ReportStatus), nullable=False, default=ReportStatus.PENDING)
    output_content = Column(Text, default="")
    output_file = Column(String(200), default="")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User")
