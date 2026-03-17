"""Event handler interface."""
from abc import ABC, abstractmethod

from src.domain.messaging.events.message_event import MessageEvent


class EventHandler(ABC):
    """事件处理器抽象基类。"""

    @abstractmethod
    async def handle(self, event: MessageEvent) -> None:
        """处理事件。

        Args:
            event: 消息事件
        """
        ...
