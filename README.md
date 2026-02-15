# Litetower

QQ Bot SDK powered by [Letoderea](https://github.com/ArcletProject/Letoderea)

基于 [Arclet Letoderea](https://github.com/ArcletProject/Letoderea) 和 [Launart](https://github.com/GraiaProject/Launart) 的 QQ 机器人 SDK。

## 特性

- 基于 Letoderea 的事件分发与依赖注入
- 使用 Launart 管理服务生命周期
- 全异步，基于 `httpx` + `uvicorn`
- 类型注解完备，支持 pyright 检查
- Rich 日志输出
- QQ 开放平台 API 封装，自动 Token 刷新

## 安装

Python 3.13+

> 当前版本尚未正式发布，PyPI 上的 `litetower` 为占位包。请从源码安装：

```bash
git clone https://github.com/sibuxiangx/Litetower.git
cd Litetower
uv sync --frozen
```

## 快速开始

```python
import arclet.letoderea as leto
from launart import Launart
from litetower import Litetower, GroupMessage, Content, Target

mgr = Launart()

bot = Litetower(
    appid="YOUR_APPID",
    clientSecret="YOUR_SECRET",
    mgr=mgr,
    sand_box=True,
)

@leto.on(GroupMessage)
async def on_group_message(app: Litetower, content: Content, target: Target):
    print(f"收到群消息: {content}")
    await app.send_group_message(target, f"你好！你说了: {content}")

if __name__ == "__main__":
    bot.launch_blocking()
```

## 核心概念

### 事件

内置事件类型：

- `GroupMessage` / `C2CMessage` — 群聊与私聊消息
- `ChannelMessage` / `DirectMessage` — 频道与频道私聊消息
- `ApplicationReady` — 应用启动完成
- `FriendAdd` / `GroupAddRobot` — 机器人关系变更

### 依赖注入

事件处理函数的参数由 Letoderea 自动注入：

- `Litetower` — 机器人实例
- `Target` — 发送目标
- `Content` — 消息内容（`str` 子类，可直接当字符串使用）
- `Author` / `Member` / `Group` — 发送者与来源信息

### 异常处理

API 调用失败抛出 `OpenAPIError`：

```python
from litetower import OpenAPIError

try:
    await app.send_group_message(...)
except OpenAPIError as e:
    print(f"发送失败: {e.code} - {e.message}")
```

## Beacon 插件系统

Litetower 内置 Beacon 插件系统，用于模块化管理事件处理。

### 启用

```python
# Beacon 由 Litetower 实例自动初始化
beacon = bot.beacon

# 加载插件
beacon.require("plugins.echo")
```

### 编写插件

```python
from litetower.beacon import listen, propagator, provider
from litetower.events.message import GroupMessage
from litetower.message.parser.base import DetectPrefix
from litetower.message.parser.msgsaw import MessageSaw, QSubResult
from litetower import Litetower

# 前缀匹配
@listen(GroupMessage)
@propagator(DetectPrefix("!hello"))
async def on_hello(event: GroupMessage, app: Litetower):
    await app.send_group_message(event.target, "Hello!")

# 指令解析
saw = MessageSaw("/echo")

@listen(GroupMessage)
@provider(saw)
async def on_echo(event: GroupMessage, result: QSubResult, app: Litetower):
    msg = " ".join(result.args) if result.args else "空"
    await app.send_group_message(event.target, f"Echo: {msg}")
```

装饰器说明：

- `@listen(Event)` — 注册事件监听器
- `@propagator(...)` — 挂载传播器，用于过滤消息（如 `DetectPrefix`、`ContainKeyword`）
- `@provider(...)` — 挂载提供者，用于解析并注入参数（如 `MessageSaw`）

## 许可证

MIT License
