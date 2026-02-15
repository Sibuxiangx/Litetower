"""lifecycle 插件 — 应用生命周期事件监听。"""

from litetower.beacon import listen
from litetower.events.builtin import ApplicationReady


@listen(ApplicationReady)
async def on_app_ready(event: ApplicationReady):
    print("[lifecycle] ✅ ApplicationReady — 机器人已就绪，可以开始处理事件")
