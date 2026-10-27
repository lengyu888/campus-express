from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

PACKAGE_TYPES = ("normal", "fragile", "large", "doc")
PACKAGE_STATUSES = ("in_stock", "picked", "overdue", "returned", "exception")
TRACKING_RE = r"^[A-Za-z0-9-]{6,40}$"
PHONE_RE = r"^1[3-9]\d{9}$"
CODE_RE = r"^\d{6}$"
SUFFIX_RE = r"^\d{4}$"


def check_phone(value: str) -> str:
    if not (value.isdigit() and len(value) == 11 and value[0] == "1"):
        raise ValueError("手机号需为 11 位数字且以 1 开头")
    return value


class PackageItem(BaseModel):
    """单个入库条目，单件入库与批量入库共用。"""

    tracking_no: str = Field(pattern=TRACKING_RE)
    recipient_phone: str = Field(pattern=PHONE_RE)
    recipient_name: str | None = Field(default=None, max_length=50)
    courier_company: str = Field(default="顺丰速运", min_length=2, max_length=30)
    package_type: Literal["normal", "fragile", "large", "doc"] = "normal"
    weight: Decimal | None = Field(default=None, ge=0, le=999.99)
    shelf_id: int | None = None
    remark: str | None = Field(default=None, max_length=255)

    @field_validator("tracking_no")
    @classmethod
    def upper_tracking(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("recipient_phone")
    @classmethod
    def check_recipient_phone(cls, v: str) -> str:
        return check_phone(v)


class PackageCreate(PackageItem):
    station_id: int


class PackageBatchCreate(BaseModel):
    station_id: int
    items: list[PackageItem] = Field(min_length=1, max_length=50)


class ShelfMove(BaseModel):
    shelf_id: int | None


class PickupVerify(BaseModel):
    pickup_code: str | None = Field(default=None, pattern=CODE_RE)
    phone_suffix: str = Field(pattern=SUFFIX_RE)
    verify_type: Literal["code_phone", "manual"] = "code_phone"
    remark: str | None = Field(default=None, max_length=200)


class ReturnIn(BaseModel):
    reason: str = Field(min_length=2, max_length=100)


class ExceptionIn(BaseModel):
    exception_type: Literal["damaged", "wrong_station", "no_phone", "other"] = "other"
    remark: str | None = Field(default=None, max_length=200)


def to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
