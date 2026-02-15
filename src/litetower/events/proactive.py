"""主动消息推送相关事件"""

from __future__ import annotations

import arclet.letoderea as leto

from litetower.events.common import get_event_target
from litetower.models.target import Target


@leto.make_event
class GroupAllowBotProactiveMessage:
    """群打开消息推送"""

    id: str
    timestamp: int
    group_openid: str
    op_member_openid: str

    @property
    def target(self) -> Target:
        return Target(target_unit=self.group_openid, event_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class GroupRejectBotProactiveMessage:
    """群关闭消息推送"""

    id: str
    timestamp: int
    group_openid: str
    op_member_openid: str

    @property
    def target(self) -> Target:
        return Target(target_unit=self.group_openid, event_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class C2CAllowBotProactiveMessage:
    """C2C 打开消息推送"""

    id: str
    timestamp: int
    user_openid: str

    @property
    def target(self) -> Target:
        return Target(target_unit=self.user_openid, event_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class C2CRejectBotProactiveMessage:
    """C2C 关闭消息推送"""

    id: str
    timestamp: int
    user_openid: str

    @property
    def target(self) -> Target:
        return Target(target_unit=self.user_openid, event_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]
