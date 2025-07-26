from pydantic import BaseModel, ConfigDict, Field
from typing import TypeVar, Generic, Any, Union, Callable
from enum import Enum
from functools import wraps
from __future__ import annotations

V = TypeVar('V')
E = TypeVar('E')

class ResultTag(str, Enum):
    OK = "ok"
    ERROR = "error"

class ResultMixin:

    def map(self, func: Callable[[Any], Any]) -> Result[Any, Any]:
        return ok(func(self.value)) if self.is_ok() else self 
    
    def map_err(self, func: Callable[[Any], Any]) -> Result[Any, Any]:
        return err(func(self.error)) if self.is_err() else self
    
    def and_then(self, func: Callable[[Any], Result[Any, Any]]) -> Result[Any, Any]:
        return func(self.value) if self.is_ok() else self

    def is_ok(self) -> bool:
        return self.tag == ResultTag.OK
    
    def is_err(self) -> bool:
        return self.tag == ResultTag.ERROR
    
    def unwrap(self):
        if self.is_ok():
            return self.value
        raise RuntimeError(f"Unwrap failed: {self.error}")
      
    def unwrap_or(self, default: Any):
        return self.value if self.is_ok() else default
    
    def expect(self, msg: str):
        if self.is_ok():
            return self.value
        raise RuntimeError(f"{msg}:{self.error}")
    


class Ok(BaseModel, Generic[V], ResultMixin):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra='forbid'
    )
    tag: ResultTag = Field(default=ResultTag.OK, frozen=True)
    value: V

class Err(BaseModel, Generic[E], ResultMixin):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra='forbid'
    )
    tag: ResultTag = Field(default=ResultTag.ERROR, frozen=True)
    error: E

Result = Union[Ok[V], Err[E]]

def ok(value: V) -> Ok[V]:
    return Ok(value=value)

def err(error: E) -> Err[E]:
    return Err(error=error)

def catch_errors(func: Callable) ->  Callable[..., Result[Any, Exception]]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Result[Any, Exception]:
        try:
            return ok(func(*args, **kwargs))
        except Exception as e:
            return err(e)
    return wrapper






