"""调试配置"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class WebHookDebugConfig(BaseModel):
    """Webhook 调试选项"""

    print_webhook_data: bool = False


class DebugConfig(BaseModel):
    """调试配置

    为 None 时表示关闭调试。
    直接使用 Optional[DebugConfig] 来表示开关，
    无需额外的 DebugFlag 包装。
    """

    webhook: WebHookDebugConfig = WebHookDebugConfig()
