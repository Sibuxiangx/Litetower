from __future__ import annotations

from typing import Any, Dict

import arclet.letoderea as leto
from ..behaviour import Behaviour
from ..cube import Cube
from ..schema import ListenerSchema


class LetodereaBehaviour(Behaviour):
    def __init__(self):
        self._subscribers: Dict[int, Any] = {}

    def allocate(self, cube: Cube) -> Any:
        if isinstance(cube.schema, ListenerSchema):
            listener = cube.content
            schema = cube.schema
            
            # Register to Letoderea
            for event_type in schema.events:
                # Letoderea.on returns a decorator, which we call with listener
                decorator = leto.on(
                    event_type,
                    providers=schema.providers,
                )
                
                subscriber = decorator(listener)
                
                # Use propagate() to add propagators so their providers() are registered
                for prog in schema.propagators:
                    subscriber.propagate(prog)
                
                self._subscribers[id(cube)] = subscriber
            
            return True
        return None

    def release(self, cube: Cube) -> Any:
        if isinstance(cube.schema, ListenerSchema):
            if id(cube) in self._subscribers:
                subscriber = self._subscribers.pop(id(cube))
                if hasattr(subscriber, "dispose"):
                    subscriber.dispose()
                else:
                    from litetower.logging import logger
                    logger.warning(f"Subscriber {subscriber} has no dispose method.")
            return True
        return None
