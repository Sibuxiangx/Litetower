"""proactive 插件 — 主动消息推送开关事件监听。"""

from litetower.beacon import listen
from litetower.events.proactive import (
    GroupAllowBotProactiveMessage,
    GroupRejectBotProactiveMessage,
    C2CAllowBotProactiveMessage,
    C2CRejectBotProactiveMessage,
)


@listen(GroupAllowBotProactiveMessage)
async def on_group_allow(event: GroupAllowBotProactiveMessage):
    print(
        f"[proactive] 📬 群 {event.group_openid} 开启主动消息推送"
        f" | 操作者: {event.op_member_openid}"
    )


@listen(GroupRejectBotProactiveMessage)
async def on_group_reject(event: GroupRejectBotProactiveMessage):
    print(
        f"[proactive] 📭 群 {event.group_openid} 关闭主动消息推送"
        f" | 操作者: {event.op_member_openid}"
    )


@listen(C2CAllowBotProactiveMessage)
async def on_c2c_allow(event: C2CAllowBotProactiveMessage):
    print(f"[proactive] 📬 用户 {event.user_openid} 开启 C2C 主动消息推送")


@listen(C2CRejectBotProactiveMessage)
async def on_c2c_reject(event: C2CRejectBotProactiveMessage):
    print(f"[proactive] 📭 用户 {event.user_openid} 关闭 C2C 主动消息推送")
