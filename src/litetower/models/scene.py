"""消息场景模型 (从 elements/normal.py 提升到 models 顶层)"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MessageScene(BaseModel):
    """消息场景信息"""

    source: Optional[str] = None
