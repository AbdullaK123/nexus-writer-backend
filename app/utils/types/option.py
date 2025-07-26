from pydantic import BaseModel, ConfigDict, Field
from typing import TypeVar, Generic, Union, Any, Callable
from enum import Enum
from functools import wraps
from __future__ import annotations

T = TypeVar('T')

class OptionTag(str, Enum):
    SOME = "some"
    EMPTY = "empty"

class OptionMixin:

    def is_some(self) -> bool:
        return self.tag == OptionTag.SOME
    
    def is_none(self) -> bool:
        return self.tag == OptionTag.EMPTY
    
    def unwrap(self):
        if self.is_some():
            return self.value
        raise RuntimeError("Can not unwrap an empty option!")
    
    def unwrap_or(self, default: Any) -> Any:
        return self.value if self.is_some() else default
    
    def map(self, func: Callable[[Any], Any]) -> Option[Any]:
        return some(func(self.value)) if self.is_some() else self
    
    def and_then(self, func: Callable[[Any], Option[Any]]) -> Option[Any]:
        return func(self.value) if self.is_some() else self
    
    def filter(self, predicate: Callable[[T], bool]) -> Option[T]:
        if self.is_some() and predicate(self.value):
            return self
        return empty()

class Some(BaseModel, Generic[T]):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra='forbid'
    )
    tag = Field(default=OptionTag.SOME, frozen=True)
    value: T


class Empty(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra='forbid'
    )
    tag = Field(default=OptionTag.EMPTY, frozen=True)


Option = Union[Some[T], Empty]

def some(value: T) -> Some[T]:
    return Some(value=value)

def empty() -> Empty:
    return Empty()

def catch_none(func: Callable) -> Callable[..., Option[T]]:
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return some(result) if result else empty()
    return wrapper
    
