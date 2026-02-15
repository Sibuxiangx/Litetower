"""消息元素定义"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class Element(BaseModel):
    """消息元素基类"""
    pass


class MediaElement(Element):
    """媒体消息元素基类"""

    data: bytes = b""
    url: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        if "data_path" in kwargs:
            path = Path(kwargs.pop("data_path"))
            kwargs["data"] = path.read_bytes()
        if "data_base64" in kwargs:
            kwargs["data"] = base64.b64decode(kwargs.pop("data_base64"))
        if "data_io" in kwargs:
            io: BytesIO = kwargs.pop("data_io")
            kwargs["data"] = io.read()
        super().__init__(**kwargs)


class Image(MediaElement):
    """图片消息"""
    pass


class Video(MediaElement):
    """视频消息"""
    pass


class Voice(MediaElement):
    """语音消息"""
    pass


class Markdown(Element):
    """Markdown 消息"""

    content: str = ""
    custom_template_id: Optional[str] = None
    params: Optional[List[Dict[str, str]]] = None

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        if self.custom_template_id:
            result: Dict[str, Any] = {"custom_template_id": self.custom_template_id}
            if self.params:
                result["params"] = self.params
            return result
        return {"content": self.content}


class KeyboardContent(BaseModel):
    """键盘内容定义"""
    content: Dict[str, Any]


class Keyboard(Element):
    """键盘消息"""

    keyboard: KeyboardContent

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return self.keyboard.content


class Ark(Element):
    """Ark 消息"""

    template_id: int
    kv: List[Dict[str, Any]]

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return {"template_id": self.template_id, "kv": self.kv}


class Embed(Element):
    """Embed 消息"""

    title: str
    prompt: Optional[str] = None
    thumbnail: Optional[Dict[str, str]] = None
    fields: Optional[List[Dict[str, str]]] = None

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {"title": self.title}
        if self.prompt:
            result["prompt"] = self.prompt
        if self.thumbnail:
            result["thumbnail"] = self.thumbnail
        if self.fields:
            result["fields"] = self.fields
        return result
