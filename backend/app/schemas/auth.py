import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

PHONE_RE = re.compile(r"^1\d{10}$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,32}$")


def validate_phone(v: str) -> str:
    if not PHONE_RE.match(v):
        raise ValueError("请输入 11 位手机号")
    return v


def validate_password(v: str) -> str:
    if not PASSWORD_RE.match(v):
        raise ValueError("密码需 8-32 位，且同时包含字母和数字")
    return v


class LoginRequest(BaseModel):
    account: str = Field(min_length=3, max_length=32, description="学号、工号或手机号")
    password: str = Field(min_length=6, max_length=64)


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    student_no: str = Field(min_length=6, max_length=20)
    name: str = Field(min_length=2, max_length=50)
    phone: str
    password: str
    college: str | None = Field(default=None, max_length=100)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password(v)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=6, max_length=64)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password(v)


class UserOut(BaseModel):
    id: int
    student_no: str | None = None
    name: str
    phone: str
    role: str
    college: str | None = None
    status: int
    last_login_at: datetime | None = None
    created_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut
