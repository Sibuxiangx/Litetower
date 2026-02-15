from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .cube import Cube


class Behaviour(ABC):
    @abstractmethod
    def allocate(self, cube: Cube) -> Any:
        pass

    @abstractmethod
    def release(self, cube: Cube) -> Any:
        pass
