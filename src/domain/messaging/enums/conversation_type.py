"""Conversation type enumeration."""
from enum import Enum


class ConversationType(str, Enum):
    """会话类型枚举。"""
    DIRECT = "direct"  # 一对一会话
    GROUP = "group"    # 群聊
