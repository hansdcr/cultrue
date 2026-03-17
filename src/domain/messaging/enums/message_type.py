"""Message type enumeration."""
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举。"""
    TEXT = "text"      # 文本消息
    IMAGE = "image"    # 图片消息
    FILE = "file"      # 文件消息
    SYSTEM = "system"  # 系统消息
