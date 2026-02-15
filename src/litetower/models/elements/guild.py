# 频道专有数据模型

from typing import List, Optional

from pydantic import BaseModel


class Mention(BaseModel):
    id: str
    username: str
    avatar: str
    bot: bool


class GuildMember(BaseModel):
    nick: Optional[str] = None
    roles: Optional[List[str]] = None
    joined_at: Optional[str] = None
