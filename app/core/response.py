from typing import Generic, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class CommonResponse(GenericModel, Generic[T]):
    success: bool
    message: str
    result: Optional[T] = None

    @classmethod
    def success_response(cls, message: str, data: Optional[T] = None):
        return cls(success=True, message=message, result=data)

    @classmethod
    def fail_response(cls, message: str, data: Optional[T] = None):
        return cls(success=False, message=message, daresultta=data)