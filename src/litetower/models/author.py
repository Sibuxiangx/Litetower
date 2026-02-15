from typing import Optional

from pydantic import BaseModel


class Author(BaseModel):
    """消息发送者"""

    # 常规聊天和频道共用字段
    id: Optional[str] = None
    union_openid: Optional[str] = None

    # 频道专有字段
    username: Optional[str] = None
    avatar: Optional[str] = None
    bot: Optional[bool] = None

    # 群专有字段
    member_openid: Optional[str] = None

    # C2C 专有字段
    user_openid: Optional[str] = None

    def ensure_avatar(self) -> None:
        if not self.avatar:
            if self.member_openid:
                self.avatar = f"https://q.qlogo.cn/qqapp/102130931/{self.member_openid}/640"
            elif self.user_openid:
                self.avatar = f"https://q.qlogo.cn/qqapp/102130931/{self.user_openid}/640"
