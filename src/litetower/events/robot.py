"""机器人和好友相关事件"""

from __future__ import annotations

import arclet.letoderea as leto

from litetower.events.common import get_event_target
from litetower.models.target import Target


@leto.make_event
class GroupDelRobot:
    """群删除机器人"""

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
class GroupAddRobot:
    """群添加机器人"""

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
class FriendAdd:
    """好友添加"""

    id: str
    user_openid: str
    timestamp: int

    @property
    def target(self) -> Target:
        return Target(target_unit=self.user_openid, event_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]


@leto.make_event
class FriendDel:
    """好友删除"""

    id: str
    user_openid: str
    timestamp: int

    @property
    def target(self) -> Target:
        return Target(target_unit=self.user_openid, event_id=self.id)

    providers = [
        leto.provide(Target, "target", call=get_event_target),
    ]
