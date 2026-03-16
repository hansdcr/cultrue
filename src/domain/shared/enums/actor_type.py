"""Actor type enumeration."""
from enum import Enum


class ActorType(str, Enum):
    """Actor类型枚举。"""
    USER = "user"
    AGENT = "agent"
