from typing import List, Union, TypeVar, Callable, Any, cast
from arclet.letoderea import Propagator, Provider, ProviderFactory

from .channel import Channel
from .cube import Cube
from .manager import Beacon
from .schema import ListenerSchema

def require(module: str):
    return Beacon.current().require(module)

T = TypeVar("T")

def propagator(*propagators: Propagator):
    """Decorator to add propagators to a listener."""
    def wrapper(func: T) -> T:
        f = cast(Any, func)
        if not hasattr(f, "__litetower_propagators__"):
            f.__litetower_propagators__ = []
        f.__litetower_propagators__.extend(propagators)
        return func
    return wrapper

def provider(*providers: Union[Provider, Any]):
    """Decorator to add providers to a listener."""
    def wrapper(func: T) -> T:
        f = cast(Any, func)
        if not hasattr(f, "__litetower_providers__"):
            f.__litetower_providers__ = []
        f.__litetower_providers__.extend(providers)
        return func
    return wrapper

def listen(*events, priority: int = 16):
    """Decorator to register an event listener to the current channel."""
    def wrapper(func):
        channel = Channel.current()
        propagators = getattr(func, "__litetower_propagators__", [])
        providers = list(getattr(func, "__litetower_providers__", []))

        # 若 propagator 同时实现了 ProviderFactory，自动注册为 provider
        for p in propagators:
            if isinstance(p, ProviderFactory) and p not in providers:
                providers.append(p)
        
        schema = ListenerSchema(
            events=list(events), 
            priority=priority,
            propagators=propagators,
            providers=providers
        )
        channel.content.append(Cube(func, schema))
        return func
    return wrapper
