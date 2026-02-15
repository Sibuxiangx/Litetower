from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from .schema import BaseSchema

T = TypeVar("T")


@dataclass
class Cube(Generic[T]):
    content: T
    schema: BaseSchema
