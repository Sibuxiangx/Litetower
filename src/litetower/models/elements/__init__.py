from litetower.models.elements.normal import (
    Group as Group,
    Member as Member,
)
from litetower.models.elements.guild import (
    Mention as Mention,
    GuildMember as GuildMember,
)

from typing import List, Optional

from pydantic import BaseModel, RootModel


class Attachment(BaseModel):
    id: Optional[str] = "C2CNOID"
    url: str
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    size: int
    content_type: str

    async def to_data_bytes(self, http_client: object | None = None) -> bytes:
        """将附件转换为字节数据。需要传入 httpx AsyncClient 实例。"""
        from httpx import AsyncClient

        if http_client is None:
            raise ValueError("需要提供 http_client 来下载附件")
        assert isinstance(http_client, AsyncClient)
        url = self.url if self.url.startswith("http") else "http://" + self.url
        return (await http_client.get(url)).content


class Attachments(RootModel[List[Attachment]]):
    """消息附件"""

    @property
    def attachments(self) -> List[Attachment]:
        return self.root
