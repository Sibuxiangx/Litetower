"""消息事件定义"""

from __future__ import annotations

from dataclasses import field
from typing import List, Optional

import arclet.letoderea as leto

from litetower.events.common import get_event_target
from litetower.models.author import Author
from litetower.models.content import Content
from litetower.models.elements import Attachments
from litetower.models.elements.guild import GuildMember, Mention
from litetower.models.elements.normal import Group, Member
from litetower.models.scene import MessageScene
from litetower.models.target import Target


@leto.make_event
class GroupMessage:
    """群消息事件"""

    id: str
    content: Content
    timestamp: str
    author: Author
    group: Group
    member: Member
    message_scene: Optional[MessageScene] = None
    attachments: Optional[Attachments] = None

    @property
    def target(self) -> Target:
        return Target(target_unit=self.group.group_openid, target_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class C2CMessage:
    """C2C 消息事件"""

    id: str
    content: Content
    timestamp: str
    author: Author
    message_scene: Optional[MessageScene] = None
    attachments: Optional[Attachments] = None

    @property
    def target(self) -> Target:
        assert self.author.user_openid
        return Target(target_unit=self.author.user_openid, target_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class ChannelMessage:
    """子频道消息事件"""

    id: str
    content: Content
    timestamp: str
    author: Author
    channel_id: str
    guild_id: str
    mentions: List[Mention] = field(default_factory=list)
    member: GuildMember = field(default_factory=GuildMember)
    attachments: Optional[Attachments] = None
    seq: int = 0
    seq_in_channel: int = 0

    @property
    def target(self) -> Target:
        return Target(target_unit=self.channel_id, target_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class DirectMessage:
    """频道私聊消息事件"""

    id: str
    content: Content
    timestamp: str
    author: Author
    channel_id: str
    guild_id: str
    member: GuildMember = field(default_factory=GuildMember)
    attachments: Optional[Attachments] = None
    seq: int = 0
    seq_in_channel: int = 0
    direct_message: bool = False
    src_guild_id: str = ""

    @property
    def target(self) -> Target:
        return Target(target_unit=self.guild_id, target_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


