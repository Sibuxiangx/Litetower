from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

from .behaviour import Behaviour
from .channel import Channel, _current_channel
from litetower.logging import logger


class Beacon:
    channels: Dict[str, Channel]
    behaviours: List[Behaviour]
    
    _instance: Optional["Beacon"] = None

    def __init__(self):
        self.channels = {}
        self.behaviours = []

    @classmethod
    def current(cls) -> "Beacon":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def require(self, module: str) -> Union[Channel, Any]:
        """Import a module as a Beacon Channel."""
        if module in self.channels:
            channel = self.channels[module]
            return channel._export or channel

        channel = Channel(module)
        token = _current_channel.set(channel)
        
        try:
            logger.debug(f"Loading module: {module}")
            if module in sys.modules:
                imported_module = importlib.reload(sys.modules[module])
            else:
                imported_module = importlib.import_module(module)
            
            # Process cubes with registered behaviours
            for cube in channel.content:
                for behaviour in self.behaviours:
                    try:
                        behaviour.allocate(cube)
                    except Exception as e:
                        logger.error(f"Error allocating cube {cube}: {e}")
                        raise

            self.channels[module] = channel
            logger.info(f"Module loaded: {module}")
            
            return channel._export or channel
            
        except Exception as e:
            logger.exception(f"Failed to load module {module}: {e}")
            # Cleanup if failed
            if module in sys.modules:
                del sys.modules[module]
            raise
        finally:
            _current_channel.reset(token)

    def install_behaviour(self, behaviour: Behaviour):
        self.behaviours.append(behaviour)

    def uninstall_channel(self, channel: Channel):
        if channel.module not in self.channels:
            return

        # Release cubes
        for cube in channel.content:
            for behaviour in self.behaviours:
                try:
                    behaviour.release(cube)
                except Exception as e:
                    logger.error(f"Error releasing cube {cube}: {e}")

        del self.channels[channel.module]
        if channel.module in sys.modules:
            del sys.modules[channel.module]
        
        logger.info(f"Module unloaded: {channel.module}")

    def reload_channel(self, channel: Channel):
        module_name = channel.module
        self.uninstall_channel(channel)
        self.require(module_name)
