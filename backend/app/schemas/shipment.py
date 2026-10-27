from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

PHONE_RE = r"^1[3-9]\d{9}$"


class ShipmentCreate(BaseModel):
    station_id: int
    receiver_name: str = Field(min_length=2, max_length=50)
    receiver_phone: str = Field(pattern=PHONE_RE)
    receiver_address: str = Field(min_length=5, max_length=200)
    item_name: str = Field(min_length=1, max_length=100)
    weight: Decimal = Field(ge=0.1, le=999.99)
    courier_company: str | None = Field(default=None, max_length=30)
    remark: str | None = Field(default=None, max_length=255)

    @field_validator("receiver_phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        if not (v.isdigit() and len(v) == 11 and v[0] == "1"):
            raise ValueError("手机号需为 11 位数字且以 1 开头")
        return v


class ShipmentAccept(BaseModel):
    weight: Decimal | None = Field(default=None, ge=0.1, le=999.99)
    courier_company: str | None = Field(default=None, max_length=30)
    freight: Decimal | None = Field(default=None, ge=0, le=9999)


class AnnouncementIn(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    content: str = Field(min_length=2, max_length=5000)
    status: int = Field(default=1, ge=0, le=1)


def to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
