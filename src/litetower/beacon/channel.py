from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Callable, List, Optional, Type, Union

from .cube import Cube
from .schema import BaseSchema

_current_channel: ContextVar["Channel"] = ContextVar("beacon_current_channel")


class Channel:
    module: str
    name: str
    author: List[str]
    description: str
    version: str
    
    content: List[Cube]
    
    _export: Any = None

    def __init__(self, module: str):
        self.module = module
        self.name = module
        self.author = []
        self.description = ""
        self.version = "0.0.1"
        self.content = []

    @staticmethod
    def current() -> "Channel":
        try:
            return _current_channel.get()
        except LookupError:
            raise RuntimeError("No active channel context. Are you using @listen inside a module loaded by Beacon?") from None

    def use(self, schema: BaseSchema) -> Callable[[Any], Any]:
        def wrapper(target: Any) -> Any:
            self.content.append(Cube(target, schema))
            return target
        return wrapper
    
    def export(self, target: Any) -> Any:
        self._export = target
        return target
