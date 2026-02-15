from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class Content(str):
    """消息内容封装

    继承自 str，因此可以直接当作字符串使用 (e.g. print(content), content.startswith("/"))。
    同时作为一个独立的类，可以用于 Letoderea 的依赖注入和类型调度。
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )

    def __repr__(self) -> str:
        return f"Content({super().__repr__()})"
