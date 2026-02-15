"""Httpx HTTP 客户端服务 (Launart)"""

from __future__ import annotations

from launart import Service, Launart
from httpx import AsyncClient
from litetower.logging import logger


class HttpxService(Service):
    """HTTP 客户端服务，通过 Launart 管理生命周期。"""

    id = "litetower.services/httpx"
    supported_interface_types = set()

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.async_client: AsyncClient = None  # type: ignore[assignment]
        self.async_client_safe: AsyncClient = None  # type: ignore[assignment]
        super().__init__()

    @property
    def required(self) -> set[str]:
        return set()

    @property
    def stages(self) -> set[str]:
        return {"preparing", "cleanup"}

    async def launch(self, manager: Launart) -> None:
        async with self.stage("preparing"):
            self.async_client = AsyncClient(timeout=self.timeout)
            self.async_client_safe = AsyncClient(timeout=self.timeout, verify=False)
            logger.info("HTTP 客户端已启动")

        async with self.stage("cleanup"):
            await self.async_client.aclose()
            await self.async_client_safe.aclose()
            logger.info("HTTP 客户端已关闭")
