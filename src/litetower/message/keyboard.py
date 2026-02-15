"""键盘消息结构定义"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RenderData(BaseModel):
    """按钮显示数据"""

    label: str
    """按钮上的文字"""
    visited_label: str
    """点击后按钮的文字"""
    style: int
    """按钮样式: 0 灰色线框, 1 蓝色线框"""


class Permission(BaseModel):
    """按钮权限"""

    type: int
    """权限类型: 0 群主/群管, 1 仅群主, 2 所有人, 3 指定uid"""
    specify_role_ids: Optional[List[str]] = None
    specify_user_ids: Optional[List[str]] = None


class Action(BaseModel):
    """按钮行为"""

    type: int
    """行为类型: 0 跳转, 1 回调, 2 指令"""
    permission: Permission
    data: str
    """操作相关的数据"""
    reply: bool = False
    """是否弹出子频道回复"""
    enter: bool = False
    """是否自动发送"""
    unsupport_tips: str = ""
    """不支持时的提示文字"""


class Button(BaseModel):
    """按钮"""

    id: Optional[str] = None
    render_data: RenderData
    action: Action


class ButtonRow(BaseModel):
    """按钮行"""

    buttons: List[Button]


class KeyboardPayload(BaseModel):
    """键盘消息数据"""

    id: Optional[str] = None
    content: Optional[Dict[str, Any]] = None

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        if self.id:
            return {"id": self.id}
        if self.content:
            return {"content": self.content}
        return {}
