"""消息内容前缀/后缀/关键字检测器。

基于 Letoderea Propagator (前置传播) + Propagator.providers 实现：
- 匹配成功时将结果以 ``text: str`` (按名注入) 和 ``MatchResult`` (按类型注入) 两种方式提供
- 不匹配时 raise STOP 中止当前订阅者

用法 (按名注入)::

    @listen(GroupMessage)
    @propagator(DetectPrefix("!hello"))
    async def handler(event: GroupMessage, text: str):
        ...

用法 (按类型注入)::

    @listen(GroupMessage)
    @propagator(DetectPrefix("!hello"))
    async def handler(event: GroupMessage, result: MatchResult):
        print(result.text)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, List, Union

from arclet.letoderea import (
    Propagator,
    Provider,
    STOP,
    provide,
)
from litetower.models.content import Content


# ───────────────── 匹配结果类型 ─────────────────

_MATCH_RESULT_KEY = "$litetower_match_result"
"""Context 中存储 MatchResult 的内部键。"""


@dataclass
class MatchResult:
    """内容匹配结果。

    Attributes:
        text: 去除匹配部分后的内容
    """

    text: str


# ───────────────── 辅助函数 ─────────────────


def _get_text(event: Any) -> tuple[Any, str]:
    """从事件中提取原始 content 及其 str 形式。"""
    raw = getattr(event, "content", None)
    return raw, (str(raw) if raw is not None else "")


def _wrap(raw: Any, text: str) -> str:
    """保持与原始 content 相同的类型。"""
    return Content(text) if isinstance(raw, Content) else text


# ───────────────── 基类 ─────────────────


class _ContentMatcher(Propagator):
    """匹配器公共基类 — 同时作为 Propagator。

    子类只需覆写 ``_check(text: str) -> tuple[bool, str]``。
    """

    def _check(self, text: str) -> tuple[bool, str]:
        """尝试匹配内容。

        Returns:
            (matched, stripped): matched 是否匹配；stripped 为处理后的字符串。
        """
        raise NotImplementedError

    # -- Propagator --

    def compose(self) -> Generator:
        def _prepend(event: Any) -> dict[str, Any]:
            raw, text = _get_text(event)
            matched, stripped = self._check(text)
            if not matched:
                raise STOP
            result = MatchResult(text=_wrap(raw, stripped))
            return {_MATCH_RESULT_KEY: result, "text": result.text}

        yield _prepend, True

    def providers(self) -> list[Provider[Any]]:
        return [
            provide(
                MatchResult,
                call=lambda ctx: ctx.get(_MATCH_RESULT_KEY),
            )
        ]


# ───────────────── 具体实现 ─────────────────


class DetectPrefix(_ContentMatcher):
    """前缀检测器。

    匹配成功后注入 ``text`` — 去除前缀并 strip 后的内容。
    """

    def __init__(self, prefix: Union[str, List[str]]):
        self.prefixes = [prefix] if isinstance(prefix, str) else prefix

    def _check(self, text: str) -> tuple[bool, str]:
        for p in self.prefixes:
            if text.startswith(p):
                return True, text[len(p) :].lstrip()
        return False, ""


class DetectSuffix(_ContentMatcher):
    """后缀检测器。

    匹配成功后注入 ``text`` — 去除后缀并 strip 后的内容。
    """

    def __init__(self, suffix: Union[str, List[str]]):
        self.suffixes = [suffix] if isinstance(suffix, str) else suffix

    def _check(self, text: str) -> tuple[bool, str]:
        for s in self.suffixes:
            if text.endswith(s):
                return True, text[: -len(s)].rstrip()
        return False, ""


class ContainKeyword(_ContentMatcher):
    """关键字包含检测器。

    匹配成功后注入 ``text`` — 原始内容 (未去除关键字)。
    """

    def __init__(self, keyword: str):
        self.keyword = keyword

    def _check(self, text: str) -> tuple[bool, str]:
        if self.keyword in text:
            return True, text
        return False, ""


class QCommandMatcher(_ContentMatcher):
    """QQ 指令匹配器 (``/cmd`` 格式)。

    匹配成功后注入 ``text`` — 去除指令部分后的参数内容。
    """

    def __init__(self, command: str):
        self.command = command

    def _check(self, text: str) -> tuple[bool, str]:
        text = text.strip()
        cmd = f"/{self.command}"
        if text == cmd:
            return True, ""
        if text.startswith(cmd + " "):
            return True, text[len(cmd) + 1 :].strip()
        return False, ""

