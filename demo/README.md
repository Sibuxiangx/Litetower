# Litetower Demo

Basic example of a bot using Litetower framework and Beacon plugin system.

## Structure

- `bot.py`: Main entry point. Initializes bot, Beacon, and auto-loads all plugins.
- `plugins/echo.py`: 消息回显 — C2C/群消息的 `!hello`、`/echo`、`ping` 指令
- `plugins/lifecycle.py`: 生命周期 — `ApplicationReady` 就绪事件
- `plugins/robot.py`: 机器人关系 — 群添加/移除机器人、好友添加/删除
- `plugins/proactive.py`: 主动消息推送 — 群/C2C 推送开关事件
- `plugins/guild.py`: 频道消息 — 子频道消息、频道私聊消息
- `plugins/msglog.py`: 消息日志 — 所有消息类型的调试日志打印

## Events Covered

| Plugin      | Events                                                                                |
| ----------- | ------------------------------------------------------------------------------------- |
| echo        | `C2CMessage`, `GroupMessage`                                                          |
| lifecycle   | `ApplicationReady`                                                                    |
| robot       | `GroupAddRobot`, `GroupDelRobot`, `FriendAdd`, `FriendDel`                             |
| proactive   | `GroupAllowBotProactiveMessage`, `GroupRejectBotProactiveMessage`, `C2CAllowBotProactiveMessage`, `C2CRejectBotProactiveMessage` |
| guild       | `ChannelMessage`, `DirectMessage`                                                     |
| msglog      | `GroupMessage`, `C2CMessage`, `ChannelMessage`, `DirectMessage`                        |

## Usage

1. Set environment variables:
   ```bash
   export QQBOT_APPID=your_appid
   export QQBOT_SECRET=your_secret
   # export QQBOT_TOKEN=your_token (if needed)
   ```

2. Run the bot:
   ```bash
   uv run demo/bot.py
   ```
