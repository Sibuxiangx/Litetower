"""Webhook 事件处理与分发。

处理从 QQ 开放平台接收的 webhook 请求，
解析为事件对象并通过 Letoderea 发布。
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional, Type

import arclet.letoderea as leto
from litetower.logging import logger
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from litetower.config.debug import DebugConfig
from litetower.events.message import (
    C2CMessage,
    ChannelMessage,
    DirectMessage,
    GroupMessage,
)
from litetower.events.proactive import (
    C2CAllowBotProactiveMessage,
    C2CRejectBotProactiveMessage,
    GroupAllowBotProactiveMessage,
    GroupRejectBotProactiveMessage,
)
from litetower.events.robot import (
    FriendAdd,
    FriendDel,
    GroupAddRobot,
    GroupDelRobot,
)
from litetower.models.author import Author
from litetower.models.content import Content
from litetower.models.elements import Attachments
from litetower.models.elements.guild import GuildMember
from litetower.models.elements.normal import Group, Member
from litetower.models.scene import MessageScene
from litetower.models.webhook import EventData, Payload


# ===== 事件工厂函数 =====

def _make_group_message(d: EventData, payload_id: str) -> GroupMessage:
    return GroupMessage(
        id=d.id or payload_id,
        content=Content(d.content or ""),
        timestamp=str(d.timestamp or ""),
        author=d.author or Author(),
        group=Group(
            group_id=d.group_id or "",
            group_openid=d.group_openid or "",
        ),
        member=Member(member_openid=d.author.member_openid or "" if d.author else ""),
        message_scene=d.message_scene,
        attachments=d.attachments,
    )


def _make_c2c_message(d: EventData, payload_id: str) -> C2CMessage:
    author = d.author or Author()
    if d.openid:
        author.user_openid = d.openid
    return C2CMessage(
        id=d.id or payload_id,
        content=Content(d.content or ""),
        timestamp=str(d.timestamp or ""),
        author=author,
        message_scene=d.message_scene,
        attachments=d.attachments,
    )


def _make_channel_message(d: EventData, payload_id: str) -> ChannelMessage:
    member = d.member if isinstance(d.member, GuildMember) else GuildMember()
    return ChannelMessage(
        id=d.id or payload_id,
        content=Content(d.content or ""),
        timestamp=str(d.timestamp or ""),
        author=d.author or Author(),
        channel_id=d.channel_id or "",
        guild_id=d.guild_id or "",
        mentions=d.mentions or [],
        member=member,
        attachments=d.attachments,
        seq=d.seq or 0,
        seq_in_channel=d.seq_in_channel or 0,
    )


def _make_direct_message(d: EventData, payload_id: str) -> DirectMessage:
    member = d.member if isinstance(d.member, GuildMember) else GuildMember()
    return DirectMessage(
        id=d.id or payload_id,
        content=Content(d.content or ""),
        timestamp=str(d.timestamp or ""),
        author=d.author or Author(),
        channel_id=d.channel_id or "",
        guild_id=d.guild_id or "",
        member=member,
        attachments=d.attachments,
        seq=d.seq or 0,
        seq_in_channel=d.seq_in_channel or 0,
        direct_message=d.direct_message or False,
        src_guild_id=d.src_guild_id or "",
    )


def _make_group_event(cls: type) -> Callable[[EventData, str], Any]:
    """通用群事件工厂 (机器人增删 / 主动消息开关)"""
    def factory(d: EventData, payload_id: str) -> Any:
        return cls(
            id=payload_id,
            timestamp=int(d.timestamp or 0),
            group_openid=d.group_openid or "",
            op_member_openid=d.op_member_openid or "",
        )
    return factory


def _make_c2c_event(cls: type) -> Callable[[EventData, str], Any]:
    """通用 C2C 事件工厂 (主动消息开关)"""
    def factory(d: EventData, payload_id: str) -> Any:
        return cls(
            id=payload_id,
            timestamp=int(d.timestamp or 0),
            user_openid=d.openid or "",
        )
    return factory


def _make_friend_event(cls: type) -> Callable[[EventData, str], Any]:
    """通用好友事件工厂"""
    def factory(d: EventData, payload_id: str) -> Any:
        return cls(
            id=payload_id,
            user_openid=d.openid or "",
            timestamp=int(d.timestamp or 0),
        )
    return factory


# ===== 事件类型映射 =====

EVENT_MAP: Dict[str, tuple[str, Callable[[EventData, str], Any]]] = {
    # 消息
    "GROUP_AT_MESSAGE_CREATE": ("群消息", _make_group_message),
    "C2C_MESSAGE_CREATE":     ("C2C消息", _make_c2c_message),
    "AT_MESSAGE_CREATE":      ("子频道消息", _make_channel_message),
    "DIRECT_MESSAGE_CREATE":  ("频道私聊", _make_direct_message),
    # 主动消息
    "GROUP_MSG_RECEIVE": ("群消息推送开启", _make_group_event(GroupAllowBotProactiveMessage)),
    "GROUP_MSG_REJECT":  ("群消息推送关闭", _make_group_event(GroupRejectBotProactiveMessage)),
    "C2C_MSG_RECEIVE":   ("C2C推送开启", _make_c2c_event(C2CAllowBotProactiveMessage)),
    "C2C_MSG_REJECT":    ("C2C推送关闭", _make_c2c_event(C2CRejectBotProactiveMessage)),
    # 好友/机器人
    "FRIEND_ADD":       ("好友添加", _make_friend_event(FriendAdd)),
    "FRIEND_DEL":       ("好友删除", _make_friend_event(FriendDel)),
    "GROUP_ADD_ROBOT":  ("群添加机器人", _make_group_event(GroupAddRobot)),
    "GROUP_DEL_ROBOT":  ("群删除机器人", _make_group_event(GroupDelRobot)),
}


# ===== Webhook 请求处理 =====

async def postevent(
    request: Request,
    debug_config: Optional[DebugConfig],
    bot_secret: str,
) -> Response:
    """处理 webhook 事件请求"""
    try:
        data = await request.json()
    except json.JSONDecodeError:
        logger.warning("无效的 JSON 数据")
        return JSONResponse({"error": "invalid json"}, status_code=400)

    op = data.get("op")

    if debug_config and debug_config.webhook.print_webhook_data:
        logger.debug(f"Webhook 数据: {json.dumps(data, ensure_ascii=False)}")

    # OP 0: 事件分发
    if op == 0:
        try:
            payload = Payload.model_validate(data)
            event_type = payload.t
            entry = EVENT_MAP.get(event_type)
            if entry:
                label, factory = entry
                event = factory(payload.d, payload.id)
                
                # 详细事件流日志
                from litetower.logging import log_event_flow
                
                source = "Unknown"
                detail = "Dispatching"
                
                # 尝试解析事件详情
                if hasattr(event, "group") and event.group:
                    source = f"群:{event.group.group_openid}"
                elif hasattr(event, "guild_id") and event.guild_id:
                    source = f"频道:{event.guild_id}"
                elif hasattr(event, "author") and event.author:
                    source = f"用户:{event.author.id}"
                elif hasattr(event, "group_openid") and event.group_openid:
                     source = f"群:{event.group_openid}"
                elif hasattr(event, "user_openid") and event.user_openid:
                     source = f"用户:{event.user_openid}"
                elif hasattr(event, "openid") and event.openid:
                     source = f"用户:{event.openid}"
                
                # Detail
                if hasattr(event, "content") and hasattr(event, "content") and event.content:
                     # 消息内容
                     user_name = "?"
                     if hasattr(event, "member") and event.member and hasattr(event.member, "name"):
                         user_name = event.member.name
                     elif hasattr(event, "author") and event.author:
                         user_name = event.author.username or event.author.id
                     
                     detail = f"{user_name} 说: {event.content}"
                elif event_type == "GROUP_ADD_ROBOT":
                     detail = f"操作者:{getattr(event, 'op_member_openid', '?')} 入群"
                elif event_type == "GROUP_DEL_ROBOT":
                     detail = f"操作者:{getattr(event, 'op_member_openid', '?')} 移群"
                elif event_type == "FRIEND_ADD":
                     detail = "成为好友"
                elif event_type == "FRIEND_DEL":
                     detail = "删除好友"
                elif "MSG_RECEIVE" in event_type:
                     detail = "开启主动消息"
                elif "MSG_REJECT" in event_type:
                     detail = "关闭主动消息"
                elif "DIRECT_MESSAGE" in event_type:
                     detail = "收到私信"

                log_event_flow(label, source, detail)
                leto.publish(event)
        except Exception as e:
            logger.exception(f"事件处理失败: {e}")

        return JSONResponse({"status": "ok"})

    # OP 13: 签名验证
    if op == 13:
        return await _handle_signature(data, bot_secret)

    return JSONResponse({"status": "ok"})


async def _handle_signature(data: Dict[str, Any], bot_secret: str) -> Response:
    """处理签名验证请求"""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    d = data.get("d", {})
    plain_token = d.get("plain_token", "")
    event_ts = d.get("event_ts", "")

    seed = bot_secret.encode("utf-8")[:32]
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    msg = f"{event_ts}{plain_token}".encode("utf-8")
    signature = private_key.sign(msg).hex()

    return JSONResponse(
        {"plain_token": plain_token, "signature": signature},
        status_code=200,
    )
