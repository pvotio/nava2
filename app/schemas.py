from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ReportCreate(BaseModel):
    template_id: str
    input_args: dict[str, Any] = Field(default_factory=dict)


class ReportOut(BaseModel):
    hash_id: UUID
    status: str
    pdf_url: str | None = None
    output_content: str | None = None
