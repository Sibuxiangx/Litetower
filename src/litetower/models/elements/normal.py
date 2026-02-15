"""群/C2C 元素模型"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Group(BaseModel):
    """群信息"""

    group_id: str = ""
    group_openid: str = ""


class Member(BaseModel):
    """群成员信息"""

    member_openid: str = ""
