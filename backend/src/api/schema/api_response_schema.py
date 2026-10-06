"""Standard API response format"""

from typing import Generic, TypeVar

from pydantic import BaseModel

from api.schema.meta_schema import MetaAPIData

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format"""

    meta: MetaAPIData
    data: T
