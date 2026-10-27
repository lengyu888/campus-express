from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import UserOut, validate_password, validate_phone

Role = Literal["student", "staff", "admin"]


class UserCreate(BaseModel):
    student_no: str | None = Field(default=None, max_length=20)
    name: str = Field(min_length=2, max_length=50)
    phone: str
    password: str
    role: Role = "student"
    college: str | None = Field(default=None, max_length=100)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password(v)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    college: str | None = Field(default=None, max_length=100)
    role: Role | None = None


class StatusUpdate(BaseModel):
    status: Literal[0, 1]


class UserPage(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int
