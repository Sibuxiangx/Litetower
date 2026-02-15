"""QQ 认证服务 (Launart)"""

from __future__ import annotations

import asyncio
from typing import Optional

from launart import Service, Launart
from litetower.logging import logger

from litetower.models.api import AccessToken
from litetower.services.httpx import HttpxService



class QAuthService(Service):
    """QQ 认证服务，通过 Launart 管理生命周期。

    负责获取和刷新 access token。
    """

    id = "litetower.services/qauth"
    supported_interface_types = set()

    def __init__(self, appid: str, client_secret: str):
        self.appid = appid
        self.client_secret = client_secret
        self.access_token: Optional[AccessToken] = None
        self._refresh_task: Optional[asyncio.Task[None]] = None
        super().__init__()

    @property
    def required(self) -> set[str]:
        return {HttpxService.id}

    @property
    def stages(self) -> set[str]:
        return {"preparing", "cleanup"}

    @property
    def token(self) -> str:
        """当前 access token"""
        if self.access_token is None:
            raise RuntimeError("QAuthService 尚未初始化")
        return self.access_token.access_token

    async def launch(self, manager: Launart) -> None:
        async with self.stage("preparing"):
            await self._fetch_token(manager)
            logger.info(
                f"认证成功，token 有效期: {self.access_token.expires_in}s"  # type: ignore
            )
            self._refresh_task = asyncio.create_task(
                self._auth_refresh_loop(manager)
            )

        async with self.stage("cleanup"):
            if self._refresh_task:
                self._refresh_task.cancel()
                try:
                    await self._refresh_task
                except asyncio.CancelledError:
                    pass
            logger.info("认证服务已停止")

    async def _fetch_token(self, manager: Launart) -> None:
        """获取 access token"""
        httpx_service = manager.get_component(HttpxService)
        try:
            response = await httpx_service.async_client.post(
                "https://bots.qq.com/app/getAppAccessToken",
                json={"appId": self.appid, "clientSecret": self.client_secret},
            )
            data = response.json()
            self.access_token = AccessToken.model_validate(data)
        except Exception as e:
            logger.error(f"Token 获取失败: {e}")
            raise

    async def _auth_refresh_loop(self, manager: Launart) -> None:
        """自动刷新 access token"""
        while True:
            if self.access_token is None:
                await asyncio.sleep(10)
                try:
                    await self._fetch_token(manager)
                except Exception:
                    continue
                continue

            # 提前 30 秒刷新，最少等待 60 秒
            sleep_time = max(int(self.access_token.expires_in) - 30, 60)
            await asyncio.sleep(sleep_time)

            try:
                await self._fetch_token(manager)
                logger.info(
                    f"Token 刷新成功，有效期: {self.access_token.expires_in}s"
                )
            except Exception as e:
                logger.error(f"Token 刷新失败: {e}")
                # 失败后每 30 秒重试
                await asyncio.sleep(30)
