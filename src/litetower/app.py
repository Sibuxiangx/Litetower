"""核心应用模块 — Litetower 框架主入口。

使用 Letoderea 事件系统，Launart 管理服务生命周期。
"""

from __future__ import annotations

import asyncio
import itertools
import json
import time
from typing import Any, Dict, List, Literal, Optional, Union

import arclet.letoderea as leto
from launart import Service, Launart
from litetower.logging import logger, log_event_flow
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.staticfiles import StaticFiles

from litetower.config.debug import DebugConfig
from litetower.config.server import FileServerConfig, WebHookConfig
from litetower.events.builtin import ApplicationReady
from litetower.message.element import Element, MediaElement
from litetower.models.api import MessageSent, OpenAPIError
from litetower.models.target import Target
from litetower.network.qqapi import QQAPI
from litetower.network.webhook import postevent
from litetower.services.auth import QAuthService
from litetower.services.httpx import HttpxService
from litetower.services.uvicorn import UvicornService
from litetower.utils import get_msg_type
from litetower.beacon import Beacon
from litetower.beacon.builtins.letoderea import LetodereaBehaviour


class Litetower:
    """QQ 机器人框架核心类。"""

    _instance: Optional["Litetower"] = None

    @classmethod
    def current(cls) -> "Litetower":
        """获取当前 Litetower 实例"""
        if cls._instance is None:
            raise RuntimeError("Litetower 尚未初始化")
        return cls._instance

    def __init__(
        self,
        appid: str,
        clientSecret: str,
        mgr: Optional[Launart] = None,
        webhook_config: Optional[WebHookConfig] = None,
        file_server_config: Optional[FileServerConfig] = None,
        debug_config: Optional[DebugConfig] = None,
        sand_box: bool = False,
    ):
        self.appid = appid
        self.clientSecret = clientSecret
        self.sand_box = sand_box
        self.mgr = mgr or Launart()

        self.webhook_config = webhook_config or WebHookConfig()
        self.file_server_config = file_server_config or FileServerConfig()
        self.debug_config = debug_config

        self._qqapi: Optional[QQAPI] = None
        self._msg_seq = itertools.count(1)

        # 保存单例引用
        Litetower._instance = self

        # 注册全局 DI：让事件处理器可通过 app: Litetower 获取实例
        # 必须在 Beacon.require() 加载插件之前注册，否则 subscriber 编译时拿不到该 provider
        leto.global_providers.append(
            leto.provide(Litetower, call=lambda _: self)
        )

        # Initialize Beacon
        self.beacon = Beacon.current()
        self.beacon.install_behaviour(LetodereaBehaviour())

    @property
    def qqapi(self) -> QQAPI:
        """获取 QQ API 客户端"""
        if self._qqapi is None:
            raise RuntimeError("Litetower 尚未启动，无法使用 API")
        return self._qqapi

    def _build_starlette_app(self) -> Starlette:
        """构建 Starlette ASGI 应用"""
        debug_config = self.debug_config
        bot_secret = self.clientSecret

        async def webhook_handler(request: Request) -> Response:
            # 记录请求进入
            # log_event_flow("Webhook", request.client.host if request.client else "Unknown", "Received POST")
            return await postevent(request, debug_config, bot_secret)

        routes = [
            Route(self.webhook_config.postevent, webhook_handler, methods=["POST"]),
        ]

        app = Starlette(routes=routes)

        # 文件服务器
        try:
            import pathlib

            localpath = pathlib.Path(self.file_server_config.localpath)
            if localpath.exists():
                app.mount(
                    self.file_server_config.remote_url,
                    StaticFiles(directory=str(localpath)),
                    name="fileserver",
                )
        except Exception as e:
            logger.warning(f"文件服务器挂载失败: {e}")

        return app

    def launch_blocking(self) -> None:
        """阻塞式启动机器人"""
        from litetower.logging import banner
        banner()

        # 注册服务
        self.mgr.add_component(HttpxService())
        self.mgr.add_component(QAuthService(self.appid, self.clientSecret))
        self.mgr.add_component(
            UvicornService(
                self._build_starlette_app(),
                host=self.webhook_config.host,
                port=self.webhook_config.port,
            )
        )
        self.mgr.add_component(AppService(self))

        logger.info(f"Litetower 启动中 [appid={self.appid}]")
        self.mgr.launch_blocking()

    # ===== 消息发送快捷方法 =====

    async def send_group_message(
        self,
        target: Target,
        content: str = "",
        element: Optional[Element] = None,
        event_id: Optional[str] = None,
    ) -> MessageSent:
        """发送群消息"""
        msg_data = self._build_message_data(
            content, element, target.target_id, event_id
        )
        media = element if isinstance(element, MediaElement) else None
        resp = await self.qqapi.send_message(
            "group", target.target_unit, msg_data, media
        )
        return self._parse_message_sent(resp, "group", target.target_unit)

    async def send_c2c_message(
        self,
        target: Target,
        content: str = "",
        element: Optional[Element] = None,
        event_id: Optional[str] = None,
    ) -> MessageSent:
        """发送 C2C 私聊消息"""
        msg_data = self._build_message_data(
            content, element, target.target_id, event_id
        )
        media = element if isinstance(element, MediaElement) else None
        resp = await self.qqapi.send_message(
            "c2c", target.target_unit, msg_data, media
        )
        return self._parse_message_sent(resp, "c2c", target.target_unit)

    async def send_channel_message(
        self,
        target: Target,
        content: str = "",
        element: Optional[Element] = None,
    ) -> MessageSent:
        """发送子频道消息"""
        msg_data = self._build_channel_message_data(content, element, target.target_id)
        resp = await self.qqapi.send_channel_message(target.target_unit, msg_data)
        return self._parse_message_sent(resp, "channel", target.target_unit)

    async def send_dms_message(
        self,
        target: Target,
        content: str = "",
        element: Optional[Element] = None,
    ) -> MessageSent:
        """发送频道私信消息"""
        msg_data = self._build_channel_message_data(content, element, target.target_id)
        resp = await self.qqapi.send_dms_message(target.target_unit, msg_data)
        return self._parse_message_sent(resp, "dms", target.target_unit)

    async def recall_message(
        self,
        target_type: str,
        target_id: str,
        message_id: str,
        hide_tip: bool = False,
    ) -> bool:
        """撤回消息"""
        return await self.qqapi.recall_message(
            target_type, target_id, message_id, hide_tip
        )

    async def recall_group_message(
        self,
        target: Target,
        message_id: str,
        hide_tip: bool = False,
    ) -> bool:
        """撤回群消息"""
        return await self.qqapi.recall_message(
            "group", target.target_unit, message_id, hide_tip
        )

    async def recall_c2c_message(
        self,
        target: Target,
        message_id: str,
        hide_tip: bool = False,
    ) -> bool:
        """撤回 C2C 私聊消息"""
        return await self.qqapi.recall_message(
            "c2c", target.target_unit, message_id, hide_tip
        )

    async def recall_channel_message(
        self,
        target: Target,
        message_id: str,
        hide_tip: bool = False,
    ) -> bool:
        """撤回子频道消息"""
        return await self.qqapi.recall_message(
            "channel", target.target_unit, message_id, hide_tip
        )

    async def recall_dms_message(
        self,
        target: Target,
        message_id: str,
        hide_tip: bool = False,
    ) -> bool:
        """撤回频道私信消息"""
        return await self.qqapi.recall_message(
            "dms", target.target_unit, message_id, hide_tip
        )

    # ===== 内部方法 =====

    @staticmethod
    def _parse_message_sent(
        resp: Dict[str, Any], target_type: str, target_id: str
    ) -> MessageSent:
        """将 API 响应解析为 MessageSent 模型"""
        return MessageSent(
            id=resp.get("id", ""),
            timestamp=resp.get("timestamp", ""),
            target_type=target_type,
            target_id=target_id,
        )

    def _build_message_data(
        self,
        content: str,
        element: Optional[Element],
        msg_id: str,
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """构建群/C2C 消息数据"""
        from litetower.message.element import Markdown, Keyboard, Ark, Embed

        msg_type = get_msg_type(content, element)
        data: Dict[str, Any] = {
            "msg_type": msg_type,
            "msg_id": msg_id,
            "msg_seq": next(self._msg_seq),
        }

        if event_id:
            data["event_id"] = event_id
        if content:
            data["content"] = content

        if isinstance(element, Markdown):
            data["markdown"] = element.model_dump()
        elif isinstance(element, Keyboard):
            data["keyboard"] = element.model_dump()
        elif isinstance(element, Ark):
            data["ark"] = element.model_dump()
        elif isinstance(element, Embed):
            data["embed"] = element.model_dump()

        return data

    def _build_channel_message_data(
        self,
        content: str,
        element: Optional[Element],
        msg_id: str,
    ) -> Dict[str, Any]:
        """构建频道消息数据"""
        from litetower.message.element import Markdown, Keyboard, Ark, Embed

        data: Dict[str, Any] = {"msg_id": msg_id}

        if content:
            data["content"] = content

        if isinstance(element, Markdown):
            data["markdown"] = element.model_dump()
        elif isinstance(element, Keyboard):
            data["keyboard"] = element.model_dump()
        elif isinstance(element, Ark):
            data["ark"] = element.model_dump()
        elif isinstance(element, Embed):
            data["embed"] = element.model_dump()

        return data


class AppService(Service):
    """核心应用服务，在 Launart 中管理 Litetower 实例。"""

    id = "litetower.services/app"
    supported_interface_types = set()

    def __init__(self, app: Litetower):
        self.app = app
        super().__init__()

    @property
    def required(self) -> set[str]:
        return {HttpxService.id, QAuthService.id}

    @property
    def stages(self) -> set[str]:
        return {"preparing", "blocking", "cleanup"}

    async def launch(self, manager: Launart) -> None:
        async with self.stage("preparing"):
            auth_service = manager.get_component(QAuthService)
            httpx_service = manager.get_component(HttpxService)
            self.app._qqapi = QQAPI(
                auth_service=auth_service,
                http_client=httpx_service.async_client,
                sand_box=self.app.sand_box,
            )
            logger.info("QQAPI 客户端初始化完成")

            leto.publish(ApplicationReady())
            logger.info("应用就绪事件已发布")

        async with self.stage("blocking"):
            await manager.status.wait_for_sigexit()

        async with self.stage("cleanup"):
            logger.info("核心服务已停止")
