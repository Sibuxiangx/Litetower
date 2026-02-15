"""Uvicorn 服务 (Launart)"""

from __future__ import annotations

import asyncio
from typing import Any

import uvicorn
from launart import Service, Launart
from litetower.logging import logger
from starlette.applications import Starlette


class UvicornService(Service):
    """Uvicorn ASGI 服务器，通过 Launart 管理生命周期。"""

    id = "litetower.services/uvicorn"
    supported_interface_types = set()

    def __init__(self, app: Starlette, host: str = "0.0.0.0", port: int = 2077):
        self.asgi_app = app
        self.host = host
        self.port = port
        super().__init__()

    @property
    def required(self) -> set[str]:
        return set()

    @property
    def stages(self) -> set[str]:
        return {"preparing", "blocking", "cleanup"}

    async def launch(self, manager: Launart) -> None:
        config = uvicorn.Config(
            app=self.asgi_app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)

        async with self.stage("preparing"):
            logger.info(f"Uvicorn 服务准备中: {self.host}:{self.port}")

        async with self.stage("blocking"):
            logger.info(f"Uvicorn 服务启动: http://{self.host}:{self.port}")
            serve_task = asyncio.create_task(server.serve())
            try:
                await manager.status.wait_for_sigexit()
            finally:
                server.should_exit = True
                await serve_task

        async with self.stage("cleanup"):
            logger.info("Uvicorn 服务已停止")
