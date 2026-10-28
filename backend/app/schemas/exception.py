from typing import Literal

from pydantic import BaseModel, Field


class ExceptionHandle(BaseModel):
    status: Literal["processing", "resolved"]
    remark: str | None = Field(default=None, max_length=200)
    package_action: Literal["keep", "restock", "returned"] = "keep"
