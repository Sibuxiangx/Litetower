"""内置事件定义"""

from __future__ import annotations

from dataclasses import field
from typing import Optional

import arclet.letoderea as leto

from litetower.config.debug import DebugConfig


@leto.make_event
class ApplicationReady:
    """应用就绪事件"""
    pass


@leto.make_event
class DebugFlagSetup:
    """调试配置设置事件"""
    debug_config: Optional[DebugConfig] = None

    providers = [
        leto.provide(DebugConfig, "debug_config"),
    ]
