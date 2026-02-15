"""工具函数"""

from __future__ import annotations

from typing import Optional

from litetower.message.element import Ark, Element, Embed, Markdown, MediaElement


def get_msg_type(content: str = "", element: Optional[Element] = None) -> int:
    """根据消息内容和元素判断消息类型

    Returns:
        0: 文本, 2: Markdown, 3: Ark, 4: Embed, 7: 富媒体
    """
    if isinstance(element, MediaElement):
        return 7
    if isinstance(element, Markdown):
        return 2
    if isinstance(element, Ark):
        return 3
    if isinstance(element, Embed):
        return 4
    if content:
        return 0
    return 0
