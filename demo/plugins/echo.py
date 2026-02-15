"""echo 插件 — 消息回显与指令示例。"""

from litetower.beacon import listen, provider, propagator
from litetower.events.message import C2CMessage, GroupMessage
from litetower.message.element import Image
from litetower.message.parser.base import DetectPrefix, ContainKeyword, MatchResult
from litetower.message.parser.msgsaw import MessageSaw, QSubResult
from litetower.models.elements import Attachments
from litetower.models.target import Target
from litetower import Litetower
import asyncio

# ──────────────────────────────────────
#  1. C2C 消息: 前缀匹配 !hello
# ──────────────────────────────────────
@listen(C2CMessage)
@propagator(DetectPrefix("!hello"))
async def on_c2c_hello(event: C2CMessage, app: Litetower):
    print(f"[echo] C2C hello from {event.author.user_openid}: {event.content}")
    await app.send_c2c_message(event.target, "Hello from Litetower! (C2C)")


# ──────────────────────────────────────
#  2. C2C 消息: MessageSaw 指令解析 /echo
# ──────────────────────────────────────
saw_echo = MessageSaw("/echo")

@listen(C2CMessage)
@provider(saw_echo)
async def on_c2c_echo(event: C2CMessage, result: QSubResult, app: Litetower):
    print(f"[echo] C2C /echo args={result.args} raw={event.content}")
    msg = " ".join(result.args) if result.args else "Empty echo"
    await app.send_c2c_message(event.target, f"Echo: {msg}")


# ──────────────────────────────────────
#  3. 群消息: 前缀匹配 !hello
# ──────────────────────────────────────
@listen(GroupMessage)
@propagator(DetectPrefix("!hello"))
async def on_group_hello(event: GroupMessage, app: Litetower,target: Target):
    print(f"[echo] Group hello in {event.group.group_openid}: {event.content}")
    await app.send_group_message(event.target, "Hello from Litetower! (Group)")
    recall = await app.send_group_message(event.target, "This message will be recalled in 5 seconds...")
    await asyncio.sleep(5)
    await app.recall_group_message(target,recall.id)
    recall_2 = await app.send_group_message(target, "This message will be recalled in 10 seconds...")
    await asyncio.sleep(10)
    await recall_2.recall()

# ──────────────────────────────────────
#  4. 群消息: MessageSaw 指令解析 /echo
# ──────────────────────────────────────
saw_group_echo = MessageSaw("/echo")

@listen(GroupMessage)
@provider(saw_group_echo)
async def on_group_echo(event: GroupMessage, result: QSubResult, app: Litetower, attachments: Attachments):
    print(f"[echo] Group /echo args={result.args} raw={event.content}")
    msg = " ".join(result.args) if result.args else "Empty echo"
    if attachments.attachments:
        print(f"[echo] Group /echo with attachment: {attachments.attachments[0]}")
        await app.send_group_message(
            event.target,
            f"Echo: {msg}",
            element=Image(url=attachments.attachments[0].url)
        )
    else:
        await app.send_group_message(event.target, f"Echo: {msg}")


# ──────────────────────────────────────
#  5. C2C 消息: 关键词检测 "ping"
# ──────────────────────────────────────
@listen(C2CMessage)
@propagator(ContainKeyword("ping"))
async def on_c2c_ping(event: C2CMessage, app: Litetower, target: Target):
    print(f"[echo] C2C ping detected: {event.content}")
    await app.send_c2c_message(target, "pong!")


# ──────────────────────────────────────
#  6. 群消息: 关键词检测 "ping"
# ──────────────────────────────────────
@listen(GroupMessage)
@propagator(ContainKeyword("ping"))
async def on_group_ping(event: GroupMessage, app: Litetower, target: Target):
    print(f"[echo] Group ping detected: {event.content}")
    await app.send_group_message(target, "pong!")


# ──────────────────────────────────────
#  7. 群消息: 前缀匹配 !say (MatchResult 类型注入示例)
# ──────────────────────────────────────
@listen(GroupMessage)
@propagator(DetectPrefix("!say"))
async def on_group_say(event: GroupMessage, result: MatchResult, app: Litetower):
    print(f"[echo] Group !say matched, text={result.text}")
    await app.send_group_message(event.target, f"You said: {result.text}")
