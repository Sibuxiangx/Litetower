"""QQ 开放平台 API 客户端"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from litetower.logging import logger
from httpx import AsyncClient

from litetower.message.element import Element, MediaElement
from litetower.models.api import OpenAPIError
from litetower.utils import get_msg_type


class MessageTarget(str, Enum):
    """消息发送目标类型"""

    GROUP = "group"
    C2C = "c2c"
    CHANNEL = "channel"
    DMS = "dms"


# API 路径映射
API_PATHS: Dict[str, Dict[str, str]] = {
    "group": {
        "send": "/v2/groups/{target_id}/messages",
        "recall": "/v2/groups/{target_id}/messages/{message_id}",
        "file": "/v2/groups/{target_id}/files",
    },
    "c2c": {
        "send": "/v2/users/{target_id}/messages",
        "recall": "/v2/users/{target_id}/messages/{message_id}",
        "file": "/v2/users/{target_id}/files",
    },
    "channel": {
        "send": "/channels/{target_id}/messages",
        "recall": "/channels/{target_id}/messages/{message_id}",
    },
    "dms": {
        "send": "/dms/{target_id}/messages",
        "recall": "/dms/{target_id}/messages/{message_id}",
    },
}

# 撤回错误码映射
RECALL_ERRORS: Dict[int, str] = {
    10008: "pin 的消息已过期",
    10062: "MsgSvrID 无效",
    11260: "小程序发的消息不能被撤回",
    11261: "消息已过撤回时限",
    11254: "频率限制",
    11251: "QQ消息不存在",
    11252: "主动消息不能被撤回",
    50006: "非群主/管理/群创消息不能被撤回",
}


class QQAPI:
    """QQ 开放平台 HTTP API 客户端

    通过持有 auth_service 引用实现 token 自动刷新。
    API 错误统一抛出 OpenAPIError 异常。
    """

    PRODUCTION_URL = "https://api.sgroup.qq.com"
    SANDBOX_URL = "https://sandbox.api.sgroup.qq.com"

    def __init__(
        self,
        auth_service: Any,  # QAuthService — 用 Any 避免循环导入
        http_client: AsyncClient,
        sand_box: bool = False,
    ):
        self._auth_service = auth_service
        self.http_client = http_client
        self.base_url = self.SANDBOX_URL if sand_box else self.PRODUCTION_URL

    @property
    def access_token(self) -> str:
        """动态获取最新 token"""
        return self._auth_service.token

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"QQBot {self.access_token}",
            "Content-Type": "application/json",
        }

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """通用 API 请求"""
        response = await self.http_client.request(
            method,
            f"{self.base_url}{url}",
            headers=self._get_headers(),
            **kwargs,
        )
        data = response.json()

        if response.status_code >= 400:
            code = data.get("code", response.status_code)
            message = data.get("message", "Unknown error")
            raise OpenAPIError(code=code, message=message, data=data)

        return data if isinstance(data, dict) else {"result": data}

    async def send_message(
        self,
        target_type: Literal["group", "c2c"],
        target_id: str,
        message_data: Dict[str, Any],
        media_element: Optional[MediaElement] = None,
    ) -> Dict[str, Any]:
        """发送消息"""
        url = API_PATHS[target_type]["send"].format(target_id=target_id)

        if media_element and (media_element.data or media_element.url):
            file_resp = await self.upload_file(target_type, target_id, media_element)
            message_data["media"] = file_resp

        # 使用新式日志 helper
        from litetower.logging import log_message_send
        msg_id = message_data.get("msg_id", "UNKNOWN")
        log_message_send(target_type, target_id, msg_id)
        
        return await self.request("POST", url, json=message_data)

    async def send_channel_message(
        self,
        channel_id: str,
        message_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """发送子频道消息"""
        url = API_PATHS["channel"]["send"].format(target_id=channel_id)
        logger.debug(f"发送频道消息 -> [{channel_id}]")
        return await self.request("POST", url, json=message_data)

    async def send_dms_message(
        self,
        guild_id: str,
        message_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """发送频道私信消息"""
        url = API_PATHS["dms"]["send"].format(target_id=guild_id)
        logger.debug(f"发送私信消息 -> [{guild_id}]")
        return await self.request("POST", url, json=message_data)

    async def recall_message(
        self,
        target_type: str,
        target_id: str,
        message_id: str,
        hide_tip: bool = False,
    ) -> bool:
        """撤回消息"""
        from litetower.logging import log_recall

        url = API_PATHS[target_type]["recall"].format(
            target_id=target_id, message_id=message_id
        )
        params = {"hidetip": "true"} if hide_tip else {}
        try:
            await self.request("DELETE", url, params=params)
            log_recall(target_type, target_id, message_id, success=True)
            return True
        except OpenAPIError as e:
            error_msg = RECALL_ERRORS.get(e.code, f"未知错误 ({e.code})")
            log_recall(target_type, target_id, message_id, success=False)
            logger.error(f"撤回失败详情: {error_msg}")
            return False

    async def upload_file(
        self,
        target_type: Literal["group", "c2c"],
        target_id: str,
        media: MediaElement,
    ) -> Dict[str, Any]:
        """上传媒体文件"""
        url = API_PATHS[target_type]["file"].format(target_id=target_id)

        file_type = 1  # 默认图片
        from litetower.message.element import Video, Voice

        if isinstance(media, Video):
            file_type = 2
        elif isinstance(media, Voice):
            file_type = 3

        data: Dict[str, Any] = {"file_type": file_type, "srv_send_msg": False}

        if media.url:
            data["url"] = media.url
        elif media.data:
            import base64
            data["file_data"] = base64.b64encode(media.data).decode()

        return await self.request("POST", url, json=data)
