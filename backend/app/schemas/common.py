from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
