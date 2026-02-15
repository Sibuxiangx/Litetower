from pydantic import BaseModel


class Target(BaseModel):
    """回复目标"""

    target_unit: str = ""
    """精确的 openid，群消息时为群 openid，私聊消息时为用户 openid"""
    target_id: str = ""
    """被动回复消息时需要的消息 id"""
    event_id: str = ""
    """非用户主动事件触发时需要的 event_id"""
