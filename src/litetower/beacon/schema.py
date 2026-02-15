from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Type, Union
from arclet.letoderea import Provider, Propagator


@dataclass
class BaseSchema:
    pass


@dataclass
class ListenerSchema(BaseSchema):
    events: List[Type[Any]]
    priority: int = 16
    providers: List[Union[Provider, Type[Provider]]] = field(default_factory=list)
    propagators: List[Propagator] = field(default_factory=list)
