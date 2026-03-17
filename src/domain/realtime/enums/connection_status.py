"""Connection status enum."""
from enum import Enum


class ConnectionStatus(str, Enum):
    """WebSocket连接状态枚举。"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
