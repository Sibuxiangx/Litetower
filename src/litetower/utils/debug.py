"""调试信息树形打印"""

from typing import Any, Type

import inspect
from pydantic import BaseModel


def format_value(value: Any) -> str:
    """格式化值的显示"""
    if isinstance(value, bool):
        return "✓" if value else "✗"
    elif value is None:
        return "None"
    elif isinstance(value, BaseModel):
        return f"[{value.__class__.__name__}]"
    return str(value)


def get_class_doc(model: Type[BaseModel]) -> str:
    """获取类的文档字符串"""
    if model.__doc__:
        return inspect.cleandoc(model.__doc__)
    return ""


def get_field_doc(model: Type[BaseModel], field_name: str) -> str:
    """获取字段的文档字符串"""
    try:
        class_vars = vars(model)
        if field_name in class_vars:
            field_value = class_vars[field_name]
            if isinstance(field_value, property) and field_value.__doc__:
                return inspect.cleandoc(field_value.__doc__)
    except (AttributeError, TypeError):
        pass

    try:
        private_doc = getattr(model, f"_{model.__name__}__{field_name}", None)
        if isinstance(private_doc, str):
            return inspect.cleandoc(private_doc)
    except AttributeError:
        pass

    try:
        field = model.model_fields[field_name]
        if field.annotation is not None and issubclass(field.annotation, BaseModel):
            class_doc = get_class_doc(field.annotation)
            if class_doc:
                return class_doc
    except (KeyError, AttributeError, TypeError):
        pass

    try:
        field = model.model_fields[field_name]
        if field.description:
            return field.description
    except (KeyError, AttributeError):
        pass

    return ""


def print_debug_tree(
    config: BaseModel, indent: str = "", is_last: bool = True, parent_prefix: str = ""
) -> str:
    """递归地将配置对象转换为树形结构字符串"""
    output: list[str] = []
    curr_indent = parent_prefix + ("└── " if is_last else "├── ")
    next_prefix = parent_prefix + ("    " if is_last else "│   ")

    if indent == "":
        class_name = config.__class__.__name__
        class_doc = get_class_doc(config.__class__)
        output.append(f"{class_name}{' # ' + class_doc if class_doc else ''}")
        curr_indent = ""
        next_prefix = ""

    fields = list(config.model_fields.items())

    for idx, (field_name, field) in enumerate(fields):
        value = getattr(config, field_name)
        is_last_field = idx == len(fields) - 1

        doc = get_field_doc(config.__class__, field_name)
        doc_suffix = f" # {doc}" if doc else ""

        if isinstance(value, BaseModel):
            output.append(f"{curr_indent}{field_name}{doc_suffix}")
            subtree = print_debug_tree(value, indent + "  ", is_last_field, next_prefix)
            output.append(subtree)
        else:
            output.append(f"{curr_indent}{field_name}: {format_value(value)}{doc_suffix}")

    return "\n".join(output)
