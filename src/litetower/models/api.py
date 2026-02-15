"""API 模型与异常定义"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class OpenAPIError(Exception):
    """QQ 开放平台 API 错误"""

    def __init__(self, code: int, message: str, data: Optional[dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f"[{code}] {message}")


class AccessToken(BaseModel):
    """QQ 开放平台 Access Token"""

    access_token: str
    expires_in: int


class MessageSent(BaseModel):
    """消息发送响应"""

    id: str
    timestamp: str
    target_type: str = ""
    target_id: str = ""

    async def recall(self, hide_tip: bool = False) -> bool:
        """快速撤回本条消息"""
        from litetower.app import Litetower

        app = Litetower.current()
        return await app.recall_message(
            self.target_type, self.target_id, self.id, hide_tip
        )
