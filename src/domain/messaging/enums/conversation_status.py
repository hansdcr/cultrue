"""Conversation status enumeration."""
from enum import Enum


class ConversationStatus(str, Enum):
    """会话状态枚举。"""
    ACTIVE = "active"      # 活跃
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"    # 已删除
