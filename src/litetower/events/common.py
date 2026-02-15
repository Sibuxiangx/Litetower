"""事件共享工具"""

from __future__ import annotations

import arclet.letoderea as leto

from litetower.models.target import Target


def get_event_target(ctx: leto.Contexts) -> Target | None:
    """从 Contexts 中安全获取事件的 target 属性。

    所有事件模块共享此函数，避免重复定义。
    """
    event = ctx.get(leto.EVENT)
    if event is not None and hasattr(event, "target"):
        return event.target  # type: ignore[no-any-return]
    return None
