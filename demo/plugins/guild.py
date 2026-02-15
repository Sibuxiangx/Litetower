"""guild 插件 — 频道消息事件监听。"""

from litetower.beacon import listen, propagator
from litetower.events.message import ChannelMessage, DirectMessage
from litetower.message.parser.base import DetectPrefix
from litetower import Litetower


# ──────────────────────────────────────
#  子频道消息 (所有消息打印)
# ──────────────────────────────────────
@listen(ChannelMessage)
async def on_channel_message(event: ChannelMessage):
    print(
        f"[guild] 📢 子频道消息"
        f" | guild={event.guild_id} channel={event.channel_id}"
        f" | author={event.author.username or event.author.id}"
        f" | content={event.content}"
    )


# ──────────────────────────────────────
#  子频道消息: !hello 回复
# ──────────────────────────────────────
@listen(ChannelMessage)
@propagator(DetectPrefix("!hello"))
async def on_channel_hello(event: ChannelMessage, app: Litetower):
    print(f"[guild] Channel hello: {event.content}")
    await app.send_channel_message(event.target, "Hello from Litetower! (Channel)")


# ──────────────────────────────────────
#  频道私聊消息 (所有消息打印)
# ──────────────────────────────────────
@listen(DirectMessage)
async def on_direct_message(event: DirectMessage):
    print(
        f"[guild] 💌 频道私聊"
        f" | guild={event.guild_id} channel={event.channel_id}"
        f" | author={event.author.username or event.author.id}"
        f" | content={event.content}"
        f" | direct_message={event.direct_message}"
    )
