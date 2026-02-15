"""robot 插件 — 机器人与好友关系事件监听。"""

from litetower.beacon import listen
from litetower.events.robot import (
    GroupAddRobot,
    GroupDelRobot,
    FriendAdd,
    FriendDel,
)


@listen(GroupAddRobot)
async def on_group_add_robot(event: GroupAddRobot):
    print(
        f"[robot] 🤖 被添加到群 {event.group_openid}"
        f" | 操作者: {event.op_member_openid}"
        f" | 时间戳: {event.timestamp}"
    )


@listen(GroupDelRobot)
async def on_group_del_robot(event: GroupDelRobot):
    print(
        f"[robot] 🚫 被移出群 {event.group_openid}"
        f" | 操作者: {event.op_member_openid}"
        f" | 时间戳: {event.timestamp}"
    )


@listen(FriendAdd)
async def on_friend_add(event: FriendAdd):
    print(
        f"[robot] 👋 新好友 {event.user_openid}"
        f" | 时间戳: {event.timestamp}"
    )


@listen(FriendDel)
async def on_friend_del(event: FriendDel):
    print(
        f"[robot] 💔 好友删除 {event.user_openid}"
        f" | 时间戳: {event.timestamp}"
    )
