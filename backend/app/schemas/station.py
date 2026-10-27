from datetime import time

from pydantic import BaseModel, Field, field_validator

TIME_RE = r"^([01]\d|2[0-3]):[0-5]\d$"


def to_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


class StationCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9-]+$")
    name: str = Field(min_length=2, max_length=50)
    address: str = Field(min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=11)
    open_time: str = Field(pattern=TIME_RE)
    close_time: str = Field(pattern=TIME_RE)
    manager_id: int | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        if v and not (v.isdigit() and len(v) == 11):
            raise ValueError("联系电话需为 11 位数字")
        return v

    @field_validator("close_time")
    @classmethod
    def check_close(cls, v: str, info) -> str:
        open_time = info.data.get("open_time")
        if open_time and to_time(v) <= to_time(open_time):
            raise ValueError("营业结束时间必须晚于开始时间")
        return v


class StationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    address: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=11)
    open_time: str | None = Field(default=None, pattern=TIME_RE)
    close_time: str | None = Field(default=None, pattern=TIME_RE)
    manager_id: int | None = None


class StationStatus(BaseModel):
    status: int = Field(ge=0, le=1)


class ShelfCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    zone: str | None = Field(default=None, max_length=20)
    capacity: int = Field(ge=1, le=200)


class ShelfUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    zone: str | None = Field(default=None, max_length=20)
    capacity: int | None = Field(default=None, ge=1, le=200)
    status: int | None = Field(default=None, ge=0, le=1)
