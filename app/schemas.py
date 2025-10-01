from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "admin@example.com", "password": "secret"}]}
    )


class ReportCreate(BaseModel):
    template_id: str
    input_args: dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "template_id": "hello_simple",
                    "input_args": {"name": "Ava", "greeting": "Hi", "items": ["one", "two"]},
                }
            ]
        }
    )


class ReportOut(BaseModel):
    hash_id: UUID
    status: str
    pdf_url: str | None = None
