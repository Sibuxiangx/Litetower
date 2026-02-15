"""MessageSaw — 指令与子指令解析器。

重写为 Letoderea Provider 模式，将 QSubResult 注入到 Contexts 中。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import arclet.letoderea as leto
from arclet.letoderea import ProviderFactory




@dataclass
class QSubResult:
    """指令匹配结果"""

    command: str
    """匹配到的指令"""
    sub_command: Optional[str] = None
    """子指令"""
    args: List[str] = field(default_factory=list)
    """参数列表"""
    text: str = ""
    """剩余内容"""


class MessageSaw(ProviderFactory):
    """指令和子指令解析器。

    用法示例：
        saw = MessageSaw("/help", [("list", True), ("detail", False)])

        @leto.on(GroupMessage, providers=[saw])
        async def handler(result: QSubResult):
            ...
    """

    def __init__(
        self,
        command: str,
        sub_commands: Optional[List[Tuple[str, bool]]] = None,
    ):
        self.command = command
        self.sub_commands = sub_commands or []

    def parse(self, content: str) -> Optional[QSubResult]:
        """解析消息内容"""
        text = content.strip()

        # 检查指令匹配
        if not text.startswith(self.command):
            return None

        remaining = text[len(self.command):].strip()

        # 无子指令
        if not self.sub_commands:
            parts = remaining.split() if remaining else []
            return QSubResult(
                command=self.command,
                args=parts,
                text=remaining,
            )

        # 匹配子指令
        for sub_cmd, required in self.sub_commands:
            if remaining.startswith(sub_cmd):
                sub_remaining = remaining[len(sub_cmd):].strip()
                parts = sub_remaining.split() if sub_remaining else []
                return QSubResult(
                    command=self.command,
                    sub_command=sub_cmd,
                    args=parts,
                    text=sub_remaining,
                )

        # 没有匹配到子指令
        parts = remaining.split() if remaining else []
        return QSubResult(
            command=self.command,
            args=parts,
            text=remaining,
        )

    def validate(self, param: leto.Param) -> "leto.Provider[QSubResult] | None":
        """作为 ProviderFactory 使用"""
        if param.annotation is QSubResult or param.name == "result":
            return _MessageSawProvider(self)
        return None


class _MessageSawProvider(leto.Provider[QSubResult]):  # type: ignore[type-arg]
    """MessageSaw 的 Provider 实现"""

    def __init__(self, saw: MessageSaw):
        self.saw = saw
        super().__init__()

    def validate(self, param: leto.Param) -> bool:
        return param.annotation is QSubResult or param.name == "result"

    async def __call__(self, context: leto.Contexts) -> QSubResult | None:
        event = context.get(leto.EVENT)
        if event is None:
            return None
        content = getattr(event, "content", None)
        if content is None:
            content = context.get("content")
        if content is None:
            return None
        # content is now expected to be str
        if not isinstance(content, str):
            # Fallback if somehow it's not string (shouldn't happen with new event defs)
             return None
             
        result = self.saw.parse(content)
        if result is None:
            raise leto.STOP
        return result
