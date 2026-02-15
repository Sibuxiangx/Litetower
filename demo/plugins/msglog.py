"""msglog 插件 — 纯日志监听，记录所有消息事件。"""

from litetower.beacon import listen
from litetower.events.message import (
    GroupMessage,
    C2CMessage,
    ChannelMessage,
    DirectMessage,
)


@listen(GroupMessage)
async def log_group(event: GroupMessage):
    print(
        f"[msglog] 群消息"
        f" | group={event.group.group_openid}"
        f" | author={event.author.member_openid or event.author.id}"
        f" | content={event.content}"
        f" | attachments={event.attachments}"
    )


@listen(C2CMessage)
async def log_c2c(event: C2CMessage):
    print(
        f"[msglog] C2C消息"
        f" | user={event.author.user_openid}"
        f" | content={event.content}"
        f" | attachments={event.attachments}"
    )


@listen(ChannelMessage)
async def log_channel(event: ChannelMessage):
    print(
        f"[msglog] 子频道消息"
        f" | guild={event.guild_id} channel={event.channel_id}"
        f" | author={event.author.username}({event.author.id})"
        f" | content={event.content}"
        f" | seq={event.seq}"
    )


@listen(DirectMessage)
async def log_direct(event: DirectMessage):
    print(
        f"[msglog] 频道私聊"
        f" | guild={event.guild_id} channel={event.channel_id}"
        f" | author={event.author.username}({event.author.id})"
        f" | content={event.content}"
    )
