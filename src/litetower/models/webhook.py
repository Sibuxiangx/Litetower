"""Webhook 数据模型"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from litetower.models.author import Author
from litetower.models.elements import Attachment, Attachments
from litetower.models.elements.guild import GuildMember, Mention
from litetower.models.elements.normal import Group, Member
from litetower.models.scene import MessageScene


class EventData(BaseModel):
    """Webhook 事件数据体 (原 D 类)

    包含消息/事件的核心数据字段。
    """

    # 通用字段
    id: str = ""
    content: Optional[str] = None
    timestamp: Optional[Any] = None

    # 消息作者与附件
    author: Optional[Author] = None
    attachments: Optional[Attachments] = None
    message_scene: Optional[MessageScene] = None

    # 群/C2C 字段
    group_id: Optional[str] = None
    group_openid: Optional[str] = None
    openid: Optional[str] = None
    op_member_openid: Optional[str] = None
    member: Optional[Union[Member, GuildMember]] = None

    # 频道字段
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    mentions: Optional[List[Mention]] = None
    seq: Optional[int] = None
    seq_in_channel: Optional[int] = None
    direct_message: Optional[bool] = None
    src_guild_id: Optional[str] = None


class Payload(BaseModel):
    """Webhook 完整负载"""

    op: int
    id: str = ""
    t: str = ""
    d: EventData = Field(default_factory=EventData)
    s: int = 0
